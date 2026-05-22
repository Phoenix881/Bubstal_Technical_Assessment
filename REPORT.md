# Brazilian E-Commerce Analytics Report

## Executive Summary

This project analyzes the Olist Brazilian e-commerce marketplace dataset, covering approximately 100K orders from 2016 to 2018. The analysis focuses on business performance, monthly demand forecasting for the June-August 2018 holdout period, and LLM-assisted recommendations through OpenRouter.

Key results:

| Metric | Value |
|---|---:|
| Total orders | 99,441 |
| Total revenue | BRL 16,008,872.12 |
| Average order value | BRL 160.99 |
| Forecast model | seasonal_naive_trend_ensemble |
| Forecast RMSE | 484.72 orders |
| Forecast MAE | 447.00 orders |
| LLM model used | baidu/cobuddy-20260430:free |

The marketplace shows strong revenue concentration in a small set of categories, heavy dependence on credit cards and boleto payments, and meaningful logistics improvement opportunities. The demand forecast slightly underpredicted the June-August 2018 holdout period, but produced a reasonable baseline for operational planning.

## Data and Scope

The dataset contains Olist marketplace orders, order items, payments, reviews, customers, sellers, products, product category translations, and geolocation data.

Analysis window:

- Full observed order range: September 2016 to October 2018
- Forecast training cutoff: May 31, 2018
- Forecast holdout period: June 1, 2018 to August 31, 2018
- LLM context uses complete monthly revenue through August 2018 to avoid overinterpreting the very small September and October partial-month data.

Revenue is computed from `payment_value`, aggregated to order level before monthly and total calculations. Demand is measured as monthly unique order count.

## Business Performance

Total marketplace revenue was BRL 16,008,872.12 across 99,441 orders, with an average order value of BRL 160.99.

Recent complete monthly revenue in the forecast holdout period:

| Month | Revenue |
|---|---:|
| 2018-06 | BRL 1,023,880.50 |
| 2018-07 | BRL 1,066,540.75 |
| 2018-08 | BRL 1,022,425.32 |

The top revenue categories are:

| Category | Revenue | Orders |
|---|---:|---:|
| health_beauty | BRL 1,441,248.07 | 8,836 |
| watches_gifts | BRL 1,305,541.61 | 5,624 |
| bed_bath_table | BRL 1,241,681.72 | 9,417 |
| sports_leisure | BRL 1,156,656.48 | 7,720 |
| computers_accessories | BRL 1,059,272.40 | 6,689 |

These categories are the strongest candidates for inventory protection, campaign planning, and seller enablement because they combine high revenue with meaningful order volume.

## Payment Mix

Payment value is concentrated in credit card and boleto:

| Payment Type | Payment Value | Orders |
|---|---:|---:|
| credit_card | BRL 12,542,084.19 | 76,505 |
| boleto | BRL 2,869,361.27 | 19,784 |
| voucher | BRL 379,436.87 | 3,866 |
| debit_card | BRL 217,989.79 | 1,528 |
| not_defined | BRL 0.00 | 3 |

Credit card is the dominant method by value and order count. Boleto is also material, so checkout reliability and payment-status communication matter for Brazilian customer behavior.

## Customer Experience and Logistics

Customer satisfaction is generally positive, but there is a visible low-score segment:

| Metric | Value |
|---|---:|
| Reviews | 98,410 |
| Average review score | 4.09 |
| Share of scores 1-2 | 14.7% |

Delivery performance:

| Metric | Value |
|---|---:|
| Delivered orders | 96,476 |
| Average delivery time | 12.56 days |
| Late delivery share | 8.1% |

Logistics is one of the clearest improvement areas. Even with an average score of 4.09, the 14.7% share of low reviews suggests that reducing late deliveries and improving delivery communication could protect customer satisfaction.

## Geographic Demand

The largest customer states by orders are:

| State | Orders |
|---|---:|
| SP | 41,746 |
| RJ | 12,852 |
| MG | 11,635 |
| RS | 5,466 |
| PR | 5,045 |

Operational and marketing improvements should start in SP, RJ, and MG because those states contain the largest order concentrations.

## Demand Forecast

The forecasting task predicts monthly order volume for June, July, and August 2018 using training data through May 31, 2018.

The model implemented is `seasonal_naive_trend_ensemble`. It blends:

- seasonal signal from the prior year when available
- recent trend from the last 12 months
- trailing moving average from recent demand

This model is intentionally simple and explainable, which fits the short assessment window and gives leadership a transparent baseline.

Forecast results:

| Month | Predicted Orders | Actual Orders | Error |
|---|---:|---:|---:|
| 2018-06 | 5,456 | 6,167 | -711 |
| 2018-07 | 5,956 | 6,292 | -336 |
| 2018-08 | 6,218 | 6,512 | -294 |

Evaluation:

| Metric | Value |
|---|---:|
| RMSE | 484.72 |
| MAE | 447.00 |

The model underpredicted all three holdout months, especially June 2018. It is still directionally useful for capacity planning, but a production version should compare multiple model classes and include richer explanatory variables such as category mix, state-level demand, seller availability, holiday effects, and marketing seasonality.

## LLM-Assisted Recommendations

The recommendation step uses OpenRouter's OpenAI-compatible chat completion API. The project loads `OPENROUTER_API_KEY` from `.env`, builds a structured analysis context, and requests JSON recommendations.

Model used successfully:

```text
baidu/cobuddy-20260430:free
```

The final generated recommendations were:

| Priority | Action | Rationale |
|---|---|---|
| high | Increase inventory and marketing spend for top revenue categories: health_beauty, watches_gifts, bed_bath_table, sports_leisure, computers_accessories | These categories generated BRL 1,441,248.07, BRL 1,305,541.61, BRL 1,241,681.72, BRL 1,156,656.48, and BRL 1,059,272.40 respectively, representing a significant portion of total revenue BRL 16,008,872.12. |
| high | Optimize logistics to reduce late delivery share of 8.1% and average delivery time of 12.56 days | Late deliveries may impact customer satisfaction, as 14.7% of reviews are scores 1-2; improving delivery performance could increase satisfaction. |
| medium | Enhance boleto checkout process to reduce friction | Boleto accounts for BRL 2,869,361.27 across 19,784 orders, making it the second-largest payment method by value and orders. |

The code includes a deterministic fallback recommendation path. If OpenRouter is rate-limited, blocked by a provider, or returns malformed JSON, the project still returns usable recommendations and marks `model_used` with `_local_fallback`.

## Limitations

- The September and October 2018 order counts are tiny, likely representing partial or anomalous periods, so the final LLM context focuses on complete revenue through August 2018.
- The forecast is a baseline model, not a fully tuned forecasting system.
- Revenue is based on payment values, while category revenue is based on item price plus freight value. These are useful but not identical business lenses.
- OpenRouter free models can be intermittent due to provider rate limits, region restrictions, and upstream availability.
- Review comments are in Portuguese and were not semantically analyzed in this version.

## Reproducibility

Install dependencies:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Download the dataset:

```bash
curl -L --fail -o data/olist_brazilian_ecommerce.zip https://www.kaggle.com/api/v1/datasets/download/olistbr/brazilian-ecommerce
unzip -o data/olist_brazilian_ecommerce.zip -d data
```

Run tests:

```bash
.venv/bin/python -m pytest -v
```

Execute the notebook:

```bash
.venv/bin/jupyter nbconvert --execute --to notebook --inplace src/notebook.ipynb --ExecutePreprocessor.timeout=240
```

Primary artifacts:

- `src/analysis.py`: analysis, forecasting, and recommendation functions
- `src/notebook.ipynb`: executed EDA notebook with visualizations
- `outputs/analysis_summary.json`: final structured summary
- `outputs/recommendations.json`: LLM recommendation output
- `outputs/monthly_demand.csv`: monthly order demand
- `outputs/revenue_by_month.csv`: monthly revenue

