
# Data Science Coding Test: Brazilian E-Commerce Analytics

You've been hired as a data scientist at a Brazilian e-commerce marketplace. Leadership wants to understand business performance, forecast demand for next quarter, and get actionable recommendations backed by data.

You have access to ~100K real orders from 2016–2018. Your job: explore the data, build a demand forecast, and use an LLM to synthesize your findings into business recommendations.

## Time Limit

**2–3 hours.**

## Getting Started

```bash
# 1. Set up Python environment
cd data-science
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Download the dataset (requires Kaggle CLI)
pip install kaggle
python data/download_data.py

# 3. Set up OpenRouter API key (for Part 3)
cp .env.example .env
# Edit .env and add your API key from https://openrouter.ai/

# 4. Verify setup
pytest tests/test_smoke.py -v   # will fail until you implement the functions
```

Don't have a Kaggle account? Download the dataset manually from:
https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce/data

Extract the CSVs into the `data/` folder.

---

## Your Tasks

### Part 1: EDA & Business Overview (~30 min)

**File to implement:** `src/analysis.py` → `get_business_overview()`

Explore the dataset and compute key business metrics. Use `src/notebook.ipynb` to show your exploratory analysis — charts, observations, data quality notes.

See [SCHEMA.md](SCHEMA.md) for the dataset documentation.

| Function | Returns |
|----------|---------|
| `get_business_overview()` | `dict` with `total_revenue`, `total_orders`, `avg_order_value`, `revenue_by_month` (DataFrame) |

---

### Part 2: Demand Forecasting (~1 hr)

**File to implement:** `src/analysis.py` → `prepare_monthly_demand()`, `forecast_demand()`

Build a model to predict monthly order volume. The training period ends on **May 31, 2018** — your model must forecast June, July, and August 2018 (the holdout period).

You may use any forecasting method (ARIMA, SARIMA, Holt-Winters, Prophet, XGBoost, etc.). Explain your choice in the notebook.

| Function | Returns |
|----------|---------|
| `prepare_monthly_demand()` | DataFrame with `month`, `order_count` |
| `forecast_demand(train, horizon)` | `dict` with `model_name`, `predictions`, `rmse`, `mae` |

---

### Part 3: LLM-Assisted Recommendations (~45 min)

**File to implement:** `src/analysis.py` → `build_analysis_context()`, `generate_recommendations()`

Use a **free LLM via OpenRouter** to generate business recommendations based on your analysis.

1. Create a free account at [openrouter.ai](https://openrouter.ai/)
2. Get an API key and add it to your `.env` file
3. Use any free model (look for models with `:free` suffix)
4. The API uses the OpenAI-compatible format: `POST https://openrouter.ai/api/v1/chat/completions`

| Function | Returns |
|----------|---------|
| `build_analysis_context()` | `str` — structured summary of your findings |
| `generate_recommendations()` | `dict` with `model_used`, `prompt`, `recommendations` (list of 3–5 dicts with `action`, `rationale`, `priority`) |

---

## What's Already Provided (do not modify)

- `src/data_loader.py` — helpers to load all 9 CSV tables
- `src/holdout_config.py` — train/test split dates
- `tests/test_smoke.py` — type and shape checks for your functions
- `SCHEMA.md` — dataset documentation with ERD and column descriptions

---

## Evaluation Criteria

| Area | What We Look For |
|------|-----------------|
| **Correctness** | Functions return accurate results matching the specified contracts |
| **Reasoning** | Insights are specific, data-driven, and reference actual values |
| **Forecasting** | Sound methodology, justified model choice, honest performance evaluation |
| **LLM Usage** | Well-structured prompt, relevant recommendations, clean output parsing |
| **Communication** | Clear notebook with explained reasoning and informative visualizations |

**Bonus (not required):** multiple model comparison, statistical tests, geographic analysis, deeper business reasoning.

---

## Self-Check

Run the smoke tests before submitting to make sure your functions have the right structure:

```bash
cd data-science
pytest tests/test_smoke.py -v
```

---

## Project Structure

```
data-science/
├── README.md               ← You are here
├── SCHEMA.md               ← Dataset docs (read this!)
├── .env.example            ← Template for API key
├── requirements.txt        ← Python dependencies
├── data/
│   └── download_data.py    ← Downloads Olist CSVs
├── src/
│   ├── data_loader.py      ← Data loading helpers (provided)
│   ├── holdout_config.py   ← Train/test split config (provided)
│   ├── analysis.py         ← TODO: implement 5 functions
│   └── notebook.ipynb      ← TODO: your EDA and explanations
└── tests/
    └── test_smoke.py       ← Smoke tests (provided)
```

Good luck!
