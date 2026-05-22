"""Shared train/test split dates for the forecasting task."""

import pandas as pd

TRAIN_END_DATE = pd.Timestamp("2018-05-31")
HOLDOUT_START_DATE = pd.Timestamp("2018-06-01")
HOLDOUT_END_DATE = pd.Timestamp("2018-08-31")
FORECAST_HORIZON = 3

