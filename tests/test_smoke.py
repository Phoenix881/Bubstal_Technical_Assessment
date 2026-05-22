from pathlib import Path

import pandas as pd

from src.analysis import (
    build_analysis_context,
    forecast_demand,
    generate_recommendations,
    get_business_overview,
    prepare_monthly_demand,
)


def _write_fixture_data(root: Path) -> None:
    rows = [
        {
            "order_id": "o1",
            "customer_id": "c1",
            "order_status": "delivered",
            "order_purchase_timestamp": "2018-04-10 10:00:00",
            "order_approved_at": "2018-04-10 11:00:00",
            "order_delivered_carrier_date": "2018-04-11 10:00:00",
            "order_delivered_customer_date": "2018-04-15 10:00:00",
            "order_estimated_delivery_date": "2018-04-20 00:00:00",
        },
        {
            "order_id": "o2",
            "customer_id": "c2",
            "order_status": "delivered",
            "order_purchase_timestamp": "2018-05-12 10:00:00",
            "order_approved_at": "2018-05-12 11:00:00",
            "order_delivered_carrier_date": "2018-05-13 10:00:00",
            "order_delivered_customer_date": "2018-05-20 10:00:00",
            "order_estimated_delivery_date": "2018-05-18 00:00:00",
        },
        {
            "order_id": "o3",
            "customer_id": "c3",
            "order_status": "delivered",
            "order_purchase_timestamp": "2018-06-02 10:00:00",
            "order_approved_at": "2018-06-02 11:00:00",
            "order_delivered_carrier_date": "2018-06-03 10:00:00",
            "order_delivered_customer_date": "2018-06-07 10:00:00",
            "order_estimated_delivery_date": "2018-06-10 00:00:00",
        },
    ]
    pd.DataFrame(rows).to_csv(root / "olist_orders_dataset.csv", index=False)

    pd.DataFrame(
        [
            {"order_id": "o1", "payment_sequential": 1, "payment_type": "credit_card", "payment_installments": 1, "payment_value": 100.0},
            {"order_id": "o2", "payment_sequential": 1, "payment_type": "boleto", "payment_installments": 1, "payment_value": 50.0},
            {"order_id": "o3", "payment_sequential": 1, "payment_type": "credit_card", "payment_installments": 2, "payment_value": 80.0},
        ]
    ).to_csv(root / "olist_order_payments_dataset.csv", index=False)

    pd.DataFrame(
        [
            {"order_id": "o1", "order_item_id": 1, "product_id": "p1", "seller_id": "s1", "shipping_limit_date": "2018-04-12", "price": 80.0, "freight_value": 20.0},
            {"order_id": "o2", "order_item_id": 1, "product_id": "p2", "seller_id": "s1", "shipping_limit_date": "2018-05-14", "price": 40.0, "freight_value": 10.0},
            {"order_id": "o3", "order_item_id": 1, "product_id": "p1", "seller_id": "s1", "shipping_limit_date": "2018-06-04", "price": 65.0, "freight_value": 15.0},
        ]
    ).to_csv(root / "olist_order_items_dataset.csv", index=False)

    pd.DataFrame(
        [
            {"product_id": "p1", "product_category_name": "beleza_saude"},
            {"product_id": "p2", "product_category_name": "utilidades_domesticas"},
        ]
    ).to_csv(root / "olist_products_dataset.csv", index=False)

    pd.DataFrame(
        [
            {"product_category_name": "beleza_saude", "product_category_name_english": "health_beauty"},
            {"product_category_name": "utilidades_domesticas", "product_category_name_english": "housewares"},
        ]
    ).to_csv(root / "product_category_name_translation.csv", index=False)

    pd.DataFrame(
        [
            {"customer_id": "c1", "customer_unique_id": "u1", "customer_zip_code_prefix": "01001", "customer_city": "sao paulo", "customer_state": "SP"},
            {"customer_id": "c2", "customer_unique_id": "u2", "customer_zip_code_prefix": "20001", "customer_city": "rio de janeiro", "customer_state": "RJ"},
            {"customer_id": "c3", "customer_unique_id": "u3", "customer_zip_code_prefix": "01001", "customer_city": "sao paulo", "customer_state": "SP"},
        ]
    ).to_csv(root / "olist_customers_dataset.csv", index=False)

    pd.DataFrame(
        [
            {"review_id": "r1", "order_id": "o1", "review_score": 5, "review_comment_title": "", "review_comment_message": "", "review_creation_date": "2018-04-16", "review_answer_timestamp": "2018-04-17"},
            {"review_id": "r2", "order_id": "o2", "review_score": 2, "review_comment_title": "", "review_comment_message": "", "review_creation_date": "2018-05-21", "review_answer_timestamp": "2018-05-22"},
        ]
    ).to_csv(root / "olist_order_reviews_dataset.csv", index=False)

    pd.DataFrame(
        [{"seller_id": "s1", "seller_zip_code_prefix": "01001", "seller_city": "sao paulo", "seller_state": "SP"}]
    ).to_csv(root / "olist_sellers_dataset.csv", index=False)

    pd.DataFrame(
        [{"geolocation_zip_code_prefix": "01001", "geolocation_lat": -23.5, "geolocation_lng": -46.6, "geolocation_city": "sao paulo", "geolocation_state": "SP"}]
    ).to_csv(root / "olist_geolocation_dataset.csv", index=False)


def test_analysis_contracts(tmp_path, monkeypatch):
    _write_fixture_data(tmp_path)
    monkeypatch.setenv("OPENROUTER_API_KEY", "")

    overview = get_business_overview(data_dir=tmp_path)
    assert overview["total_revenue"] == 230.0
    assert overview["total_orders"] == 3
    assert isinstance(overview["revenue_by_month"], pd.DataFrame)

    demand = prepare_monthly_demand(data_dir=tmp_path)
    assert list(demand.columns) == ["month", "order_count"]

    forecast = forecast_demand(demand[demand["month"] <= "2018-05-01"], horizon=1, data_dir=tmp_path)
    assert set(forecast) == {"model_name", "predictions", "rmse", "mae"}
    assert len(forecast["predictions"]) == 1

    context = build_analysis_context(data_dir=tmp_path)
    assert "Business overview" in context

    recs = generate_recommendations(data_dir=tmp_path)
    assert 3 <= len(recs["recommendations"]) <= 5
    assert {"model_used", "prompt", "recommendations"}.issubset(recs)
