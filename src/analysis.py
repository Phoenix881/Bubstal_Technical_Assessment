"""Business analysis, forecasting, and LLM recommendations for Olist data."""

from __future__ import annotations

import json
import math
import os
import re
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional at runtime
    load_dotenv = None

try:
    from .data_loader import load_table
    from .holdout_config import FORECAST_HORIZON, HOLDOUT_END_DATE, TRAIN_END_DATE
except ImportError:  # pragma: no cover - supports running from src/ directly
    from data_loader import load_table
    from holdout_config import FORECAST_HORIZON, HOLDOUT_END_DATE, TRAIN_END_DATE


DEFAULT_OPENROUTER_MODEL = "baidu/cobuddy:free"


def _month_start(values: pd.Series) -> pd.Series:
    return pd.to_datetime(values).dt.to_period("M").dt.to_timestamp()


def _orders_with_payment_value(data_dir: str | Path | None = None) -> pd.DataFrame:
    orders = load_table("orders", data_dir=data_dir)
    payments = load_table("payments", data_dir=data_dir)

    order_payments = (
        payments.groupby("order_id", as_index=False)["payment_value"]
        .sum()
        .rename(columns={"payment_value": "order_payment_value"})
    )

    orders = orders.merge(order_payments, on="order_id", how="left")
    orders["order_payment_value"] = orders["order_payment_value"].fillna(0.0)
    orders["month"] = _month_start(orders["order_purchase_timestamp"])
    return orders


def get_business_overview(data_dir: str | Path | None = None) -> dict[str, Any]:
    """Compute topline business metrics from orders and payments."""

    orders = _orders_with_payment_value(data_dir=data_dir)

    total_orders = int(orders["order_id"].nunique())
    total_revenue = float(orders["order_payment_value"].sum())
    avg_order_value = float(total_revenue / total_orders) if total_orders else 0.0

    revenue_by_month = (
        orders.dropna(subset=["month"])
        .groupby("month", as_index=False)["order_payment_value"]
        .sum()
        .rename(columns={"order_payment_value": "revenue"})
        .sort_values("month")
        .reset_index(drop=True)
    )

    return {
        "total_revenue": round(total_revenue, 2),
        "total_orders": total_orders,
        "avg_order_value": round(avg_order_value, 2),
        "revenue_by_month": revenue_by_month,
    }


def prepare_monthly_demand(data_dir: str | Path | None = None) -> pd.DataFrame:
    """Return monthly order volume as a complete month-level time series."""

    orders = load_table("orders", data_dir=data_dir)
    orders = orders.dropna(subset=["order_purchase_timestamp"]).copy()
    orders["month"] = _month_start(orders["order_purchase_timestamp"])

    monthly = (
        orders.groupby("month", as_index=False)["order_id"]
        .nunique()
        .rename(columns={"order_id": "order_count"})
        .sort_values("month")
    )

    if monthly.empty:
        return pd.DataFrame({"month": pd.Series(dtype="datetime64[ns]"), "order_count": pd.Series(dtype="int64")})

    full_index = pd.date_range(monthly["month"].min(), monthly["month"].max(), freq="MS")
    monthly = (
        monthly.set_index("month")
        .reindex(full_index, fill_value=0)
        .rename_axis("month")
        .reset_index()
    )
    monthly["order_count"] = monthly["order_count"].astype(int)
    return monthly


def _forecast_values(train: pd.DataFrame, horizon: int) -> np.ndarray:
    y = train["order_count"].astype(float).to_numpy()
    if horizon <= 0:
        return np.array([], dtype=float)
    if len(y) == 0:
        return np.zeros(horizon, dtype=float)
    if len(y) == 1:
        return np.repeat(y[-1], horizon)

    trailing_window = min(3, len(y))
    moving_average = np.repeat(y[-trailing_window:].mean(), horizon)

    trend_window = min(12, len(y))
    x = np.arange(trend_window, dtype=float)
    slope, intercept = np.polyfit(x, y[-trend_window:], 1)
    trend_x = np.arange(trend_window, trend_window + horizon, dtype=float)
    trend_forecast = intercept + slope * trend_x

    if len(y) >= 12:
        seasonal_forecast = np.array([y[-12 + (step % 12)] for step in range(horizon)], dtype=float)
        forecast = 0.50 * seasonal_forecast + 0.30 * trend_forecast + 0.20 * moving_average
    else:
        forecast = 0.60 * moving_average + 0.40 * trend_forecast

    return np.maximum(0, np.rint(forecast))


def _evaluate_forecast(
    prediction_frame: pd.DataFrame,
    data_dir: str | Path | None = None,
) -> tuple[float, float]:
    try:
        actual = prepare_monthly_demand(data_dir=data_dir)
    except FileNotFoundError:
        return float("nan"), float("nan")

    actual = actual.rename(columns={"order_count": "actual_order_count"})
    comparison = prediction_frame.merge(actual, on="month", how="left").dropna(subset=["actual_order_count"])
    if comparison.empty:
        return float("nan"), float("nan")

    errors = comparison["predicted_order_count"] - comparison["actual_order_count"]
    rmse = float(np.sqrt(np.mean(np.square(errors))))
    mae = float(np.mean(np.abs(errors)))
    return round(rmse, 2), round(mae, 2)


def forecast_demand(
    train: pd.DataFrame,
    horizon: int = FORECAST_HORIZON,
    data_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Forecast monthly order volume for the next `horizon` months."""

    required_columns = {"month", "order_count"}
    missing = required_columns.difference(train.columns)
    if missing:
        missing_text = ", ".join(sorted(missing))
        raise ValueError(f"train is missing required columns: {missing_text}")

    train = train.copy()
    train["month"] = pd.to_datetime(train["month"])
    train = train.sort_values("month").reset_index(drop=True)

    if train.empty:
        future_months = pd.date_range(TRAIN_END_DATE.to_period("M").to_timestamp() + pd.offsets.MonthBegin(1), periods=horizon, freq="MS")
    else:
        future_months = pd.date_range(train["month"].max() + pd.offsets.MonthBegin(1), periods=horizon, freq="MS")

    forecast = _forecast_values(train, horizon=horizon)
    prediction_frame = pd.DataFrame(
        {
            "month": future_months,
            "predicted_order_count": forecast.astype(int),
        }
    )

    rmse, mae = _evaluate_forecast(prediction_frame, data_dir=data_dir)

    predictions = [
        {
            "month": row.month.strftime("%Y-%m-%d"),
            "predicted_order_count": int(row.predicted_order_count),
        }
        for row in prediction_frame.itertuples(index=False)
    ]

    return {
        "model_name": "seasonal_naive_trend_ensemble",
        "predictions": predictions,
        "rmse": rmse,
        "mae": mae,
    }


def _format_brl(value: float) -> str:
    return f"BRL {value:,.2f}"


def _optional_table(name: str, data_dir: str | Path | None = None) -> pd.DataFrame | None:
    try:
        return load_table(name, data_dir=data_dir)
    except FileNotFoundError:
        return None


def _top_categories(data_dir: str | Path | None = None, limit: int = 5) -> pd.DataFrame:
    items = _optional_table("order_items", data_dir=data_dir)
    products = _optional_table("products", data_dir=data_dir)
    translation = _optional_table("category_translation", data_dir=data_dir)
    if items is None or products is None:
        return pd.DataFrame(columns=["category", "item_revenue", "orders"])

    category_sales = items.merge(products[["product_id", "product_category_name"]], on="product_id", how="left")
    if translation is not None:
        category_sales = category_sales.merge(translation, on="product_category_name", how="left")
        category_sales["category"] = category_sales["product_category_name_english"].fillna(category_sales["product_category_name"])
    else:
        category_sales["category"] = category_sales["product_category_name"]

    category_sales["category"] = category_sales["category"].fillna("unknown")
    category_sales["item_revenue"] = category_sales["price"].fillna(0) + category_sales["freight_value"].fillna(0)

    return (
        category_sales.groupby("category", as_index=False)
        .agg(item_revenue=("item_revenue", "sum"), orders=("order_id", "nunique"))
        .sort_values("item_revenue", ascending=False)
        .head(limit)
        .reset_index(drop=True)
    )


def _payment_mix(data_dir: str | Path | None = None, limit: int = 5) -> pd.DataFrame:
    payments = _optional_table("payments", data_dir=data_dir)
    if payments is None:
        return pd.DataFrame(columns=["payment_type", "payment_value", "orders"])

    return (
        payments.groupby("payment_type", as_index=False)
        .agg(payment_value=("payment_value", "sum"), orders=("order_id", "nunique"))
        .sort_values("payment_value", ascending=False)
        .head(limit)
        .reset_index(drop=True)
    )


def _review_summary(data_dir: str | Path | None = None) -> dict[str, float | int] | None:
    reviews = _optional_table("reviews", data_dir=data_dir)
    if reviews is None or reviews.empty:
        return None

    return {
        "review_count": int(reviews["review_id"].nunique()),
        "avg_review_score": round(float(reviews["review_score"].mean()), 2),
        "low_score_share": round(float((reviews["review_score"] <= 2).mean()), 4),
    }


def _delivery_summary(data_dir: str | Path | None = None) -> dict[str, float | int] | None:
    orders = _optional_table("orders", data_dir=data_dir)
    if orders is None or orders.empty:
        return None

    delivered = orders.dropna(subset=["order_delivered_customer_date", "order_purchase_timestamp"]).copy()
    if delivered.empty:
        return None

    delivered["delivery_days"] = (
        delivered["order_delivered_customer_date"] - delivered["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400
    delivered["is_late"] = delivered["order_delivered_customer_date"] > delivered["order_estimated_delivery_date"]

    return {
        "delivered_orders": int(delivered["order_id"].nunique()),
        "avg_delivery_days": round(float(delivered["delivery_days"].mean()), 2),
        "late_delivery_share": round(float(delivered["is_late"].mean()), 4),
    }


def _top_customer_states(data_dir: str | Path | None = None, limit: int = 5) -> pd.DataFrame:
    orders = _optional_table("orders", data_dir=data_dir)
    customers = _optional_table("customers", data_dir=data_dir)
    if orders is None or customers is None:
        return pd.DataFrame(columns=["customer_state", "orders"])

    state_orders = orders.merge(customers[["customer_id", "customer_state"]], on="customer_id", how="left")
    return (
        state_orders.groupby("customer_state", as_index=False)["order_id"]
        .nunique()
        .rename(columns={"order_id": "orders"})
        .sort_values("orders", ascending=False)
        .head(limit)
        .reset_index(drop=True)
    )


def build_analysis_context(data_dir: str | Path | None = None) -> str:
    """Build a compact, structured text summary for the recommendation LLM."""

    overview = get_business_overview(data_dir=data_dir)
    monthly_demand = prepare_monthly_demand(data_dir=data_dir)
    train = monthly_demand[monthly_demand["month"] <= TRAIN_END_DATE.to_period("M").to_timestamp()]
    forecast = forecast_demand(train, horizon=FORECAST_HORIZON, data_dir=data_dir)

    revenue_by_month = overview["revenue_by_month"]
    complete_revenue = revenue_by_month[
        revenue_by_month["month"] <= HOLDOUT_END_DATE.to_period("M").to_timestamp()
    ]
    latest_revenue = complete_revenue.tail(3)
    top_categories = _top_categories(data_dir=data_dir)
    payment_mix = _payment_mix(data_dir=data_dir)
    review_summary = _review_summary(data_dir=data_dir)
    delivery_summary = _delivery_summary(data_dir=data_dir)
    top_states = _top_customer_states(data_dir=data_dir)

    lines = [
        "Brazilian e-commerce marketplace analysis context",
        "",
        "Business overview:",
        f"- Total orders: {overview['total_orders']:,}",
        f"- Total revenue: {_format_brl(float(overview['total_revenue']))}",
        f"- Average order value: {_format_brl(float(overview['avg_order_value']))}",
        f"- Date range: {monthly_demand['month'].min().date()} to {monthly_demand['month'].max().date()}",
        f"- Forecast holdout period: 2018-06-01 to {HOLDOUT_END_DATE.date()}",
        "",
        "Recent complete monthly revenue through the holdout period:",
    ]

    for row in latest_revenue.itertuples(index=False):
        lines.append(f"- {row.month.strftime('%Y-%m')}: {_format_brl(float(row.revenue))}")

    lines.extend(["", "Demand forecast for the next quarter:"])
    for item in forecast["predictions"]:
        lines.append(f"- {item['month'][:7]}: {item['predicted_order_count']:,} orders")
    if not math.isnan(float(forecast["rmse"])):
        lines.append(f"- Holdout RMSE: {forecast['rmse']}; MAE: {forecast['mae']}")

    if not top_categories.empty:
        lines.extend(["", "Top revenue categories:"])
        for row in top_categories.itertuples(index=False):
            lines.append(f"- {row.category}: {_format_brl(float(row.item_revenue))} across {int(row.orders):,} orders")

    if not payment_mix.empty:
        lines.extend(["", "Payment mix by value:"])
        for row in payment_mix.itertuples(index=False):
            lines.append(f"- {row.payment_type}: {_format_brl(float(row.payment_value))} across {int(row.orders):,} orders")

    if review_summary:
        lines.extend(
            [
                "",
                "Customer satisfaction:",
                f"- Reviews: {review_summary['review_count']:,}",
                f"- Average review score: {review_summary['avg_review_score']}",
                f"- Share of scores 1-2: {review_summary['low_score_share']:.1%}",
            ]
        )

    if delivery_summary:
        lines.extend(
            [
                "",
                "Delivery performance:",
                f"- Delivered orders: {delivery_summary['delivered_orders']:,}",
                f"- Average delivery time: {delivery_summary['avg_delivery_days']} days",
                f"- Late delivery share: {delivery_summary['late_delivery_share']:.1%}",
            ]
        )

    if not top_states.empty:
        lines.extend(["", "Largest customer states by orders:"])
        for row in top_states.itertuples(index=False):
            lines.append(f"- {row.customer_state}: {int(row.orders):,} orders")

    lines.extend(
        [
            "",
            "Recommendation requirements:",
            "- Return 3 to 5 actions.",
            "- Tie every action to the numbers above.",
            "- Include rationale and priority.",
        ]
    )

    return "\n".join(lines)


def _strip_json_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _parse_recommendations(text: str) -> list[dict[str, str]]:
    payload = json.loads(_strip_json_fences(text))
    if isinstance(payload, dict):
        recommendations = payload.get("recommendations", [])
    elif isinstance(payload, list):
        recommendations = payload
    else:
        recommendations = []

    cleaned = []
    for item in recommendations[:5]:
        if not isinstance(item, dict):
            continue
        cleaned.append(
            {
                "action": str(item.get("action", "")).strip(),
                "rationale": str(item.get("rationale", "")).strip(),
                "priority": str(item.get("priority", "medium")).strip().lower(),
            }
        )

    return [item for item in cleaned if item["action"] and item["rationale"]]


def _fallback_recommendations(context: str) -> list[dict[str, str]]:
    def section_lines(section_title: str) -> list[str]:
        lines = []
        in_section = False
        for line in context.splitlines():
            if line == section_title:
                in_section = True
                continue
            if in_section and not line.startswith("- "):
                break
            if in_section:
                lines.append(line[2:])
        return lines

    forecast_lines = []
    in_forecast_section = False
    for line in context.splitlines():
        if line == "Demand forecast for the next quarter:":
            in_forecast_section = True
            continue
        if in_forecast_section and not line.startswith("- "):
            break
        if in_forecast_section and re.search(r"orders$", line):
            forecast_lines.append(line)
    forecast_text = "; ".join(line[2:] for line in forecast_lines) or "the next-quarter forecast"
    category_text = "; ".join(section_lines("Top revenue categories:")[:3])
    payment_text = "; ".join(section_lines("Payment mix by value:")[:2])
    state_text = "; ".join(section_lines("Largest customer states by orders:")[:3])
    delivery_text = "; ".join(section_lines("Delivery performance:"))
    satisfaction_text = "; ".join(section_lines("Customer satisfaction:"))

    return [
        {
            "action": "Plan seller capacity and inventory against the three-month demand forecast.",
            "rationale": f"The forecast points to expected order volume of {forecast_text}, so operations should align staffing, inventory, and seller readiness before demand arrives.",
            "priority": "high",
        },
        {
            "action": "Prioritize the highest-revenue categories for merchandising and stock availability.",
            "rationale": f"The leading categories are {category_text}, making them the best place to protect availability and run targeted promotions.",
            "priority": "high",
        },
        {
            "action": "Reduce late deliveries and shorten fulfillment times.",
            "rationale": f"Delivery performance shows {delivery_text}; customer satisfaction shows {satisfaction_text}, so logistics improvements should protect review quality.",
            "priority": "high",
        },
        {
            "action": "Use payment mix insights to tune checkout and promotions.",
            "rationale": f"Payment value is concentrated in {payment_text}, so checkout incentives should support the payment types customers already prefer.",
            "priority": "medium",
        },
        {
            "action": "Focus regional operations on the largest customer states.",
            "rationale": f"The largest customer states are {state_text}, so regional logistics and marketing work should start where order density is highest.",
            "priority": "medium",
        },
    ]


def generate_recommendations(
    data_dir: str | Path | None = None,
    model: str = DEFAULT_OPENROUTER_MODEL,
) -> dict[str, Any]:
    """Generate actionable recommendations with OpenRouter, with a local fallback."""

    if load_dotenv is not None:
        project_root = Path(__file__).resolve().parents[1]
        load_dotenv(dotenv_path=project_root / ".env")

    env_model = os.getenv("OPENROUTER_MODEL")
    if model == DEFAULT_OPENROUTER_MODEL and env_model:
        model = env_model

    context = build_analysis_context(data_dir=data_dir)
    prompt = (
        "You are advising leadership at a Brazilian e-commerce marketplace. "
        "Use the analysis context below to produce exactly 3 concise, actionable "
        "business recommendations. Cite only exact figures that appear in the "
        "context. Do not invent, estimate, or derive new percentages or values. "
        "Return valid JSON only in this shape: "
        '{"recommendations":[{"action":"...","rationale":"...","priority":"high|medium|low"}]}.\n\n'
        f"{context}"
    )

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return {
            "model_used": "local_fallback_no_openrouter_key",
            "prompt": prompt,
            "recommendations": _fallback_recommendations(context),
        }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/",
        "X-Title": "Brazilian E-Commerce Analytics",
    }
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a data-driven strategy analyst. Return only valid JSON. "
                    "Use only numbers explicitly supplied by the user."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 1800,
        "temperature": 0.2,
        "include_reasoning": False,
    }

    try:
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=45,
                )
                response.raise_for_status()
                response_payload = response.json()
                content = response_payload["choices"][0]["message"]["content"]
                recommendations = _parse_recommendations(content)
                if len(recommendations) < 3:
                    raise ValueError("LLM returned fewer than 3 valid recommendations")
                model_used = response_payload.get("model", model)
                break
            except Exception as exc:
                last_error = exc
                if attempt < 1:
                    time.sleep(2 * (attempt + 1))
        else:
            raise last_error or RuntimeError("OpenRouter request failed")
    except Exception:
        recommendations = _fallback_recommendations(context)
        model_used = f"{model}_local_fallback"

    return {
        "model_used": model_used,
        "prompt": prompt,
        "recommendations": recommendations[:5],
    }
