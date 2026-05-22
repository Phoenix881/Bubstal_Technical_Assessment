# Brazilian E-Commerce Analytics

Data science assessment project analyzing the Olist Brazilian e-commerce marketplace dataset. The project computes core business metrics, forecasts monthly order demand for the June-August 2018 holdout period, and uses OpenRouter to generate data-grounded business recommendations.

## Deliverables

- `src/analysis.py`: five required analysis functions
- `src/notebook.ipynb`: executed EDA notebook with charts and explanations
- `REPORT.md`: final written report
- `REPORT.pdf`: PDF copy of the final report
- `outputs/analysis_summary.json`: structured final results
- `outputs/recommendations.json`: OpenRouter recommendation output
- `outputs/monthly_demand.csv`: monthly order demand
- `outputs/revenue_by_month.csv`: monthly revenue

## Key Results

| Metric | Value |
|---|---:|
| Total orders | 99,441 |
| Total revenue | BRL 16,008,872.12 |
| Average order value | BRL 160.99 |
| Forecast RMSE | 484.72 orders |
| Forecast MAE | 447.00 orders |
| LLM model used | baidu/cobuddy-20260430:free |

Forecasted order demand:

| Month | Predicted Orders | Actual Orders |
|---|---:|---:|
| 2018-06 | 5,456 | 6,167 |
| 2018-07 | 5,956 | 6,292 |
| 2018-08 | 6,218 | 6,512 |

## Repository Structure

```text
.
├── README.md
├── REPORT.md
├── REPORT.pdf
├── SCHEMA.md
├── requirements.txt
├── outputs/
│   ├── analysis_context.txt
│   ├── analysis_summary.json
│   ├── monthly_demand.csv
│   ├── recommendations.json
│   └── revenue_by_month.csv
├── src/
│   ├── analysis.py
│   ├── data_loader.py
│   ├── holdout_config.py
│   └── notebook.ipynb
└── tests/
    └── test_smoke.py
```

The raw Olist CSV files are intentionally ignored by git. Download them into `data/` before rerunning the analysis.

## Setup

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Create a local `.env` from the template:

```bash
cp .env.example .env
```

Then add your OpenRouter key:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=baidu/cobuddy:free
```

`.env` is ignored by git and should not be published.

## Download Data

The dataset can be downloaded directly from Kaggle's public dataset endpoint:

```bash
mkdir -p data
curl -L --fail -o data/olist_brazilian_ecommerce.zip https://www.kaggle.com/api/v1/datasets/download/olistbr/brazilian-ecommerce
unzip -o data/olist_brazilian_ecommerce.zip -d data
```

Expected files include:

- `data/olist_orders_dataset.csv`
- `data/olist_order_items_dataset.csv`
- `data/olist_order_payments_dataset.csv`
- `data/olist_order_reviews_dataset.csv`
- `data/olist_products_dataset.csv`
- `data/olist_customers_dataset.csv`
- `data/olist_sellers_dataset.csv`
- `data/olist_geolocation_dataset.csv`
- `data/product_category_name_translation.csv`

## Run

Run smoke tests:

```bash
.venv/bin/python -m pytest -v
```

Execute the notebook:

```bash
.venv/bin/jupyter nbconvert --execute --to notebook --inplace src/notebook.ipynb --ExecutePreprocessor.timeout=240
```

Run the analysis functions directly:

```bash
.venv/bin/python - <<'PY'
from src.analysis import get_business_overview, prepare_monthly_demand, forecast_demand, generate_recommendations
from src.holdout_config import FORECAST_HORIZON, TRAIN_END_DATE

overview = get_business_overview()
monthly = prepare_monthly_demand()
train = monthly[monthly["month"] <= TRAIN_END_DATE.to_period("M").to_timestamp()]
forecast = forecast_demand(train, horizon=FORECAST_HORIZON)
recommendations = generate_recommendations()

print(overview["total_orders"], overview["total_revenue"], overview["avg_order_value"])
print(forecast)
print(recommendations["model_used"])
PY
```

## OpenRouter Notes

This project uses OpenRouter's OpenAI-compatible chat completions API:

```text
POST https://openrouter.ai/api/v1/chat/completions
```

The default model is `baidu/cobuddy:free`, which worked during the final run from this environment. Free OpenRouter models can be intermittent because of rate limits, upstream provider availability, or regional restrictions. If a request fails or returns malformed JSON, `generate_recommendations()` returns deterministic fallback recommendations and marks `model_used` with `_local_fallback`.

## Final Report

See `REPORT.md` or `REPORT.pdf` for the complete project write-up.

