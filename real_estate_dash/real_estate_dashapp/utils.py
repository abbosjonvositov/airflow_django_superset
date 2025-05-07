from joblib import load
import pandas as pd
from django.conf import settings
import os
import numpy as np
from django.core.cache import cache
# import xgboost as xgb

shared_data_path = os.path.join(settings.BASE_DIR, '..', 'shared_data', 'pkls')
shared_data_path = os.path.abspath(shared_data_path)  # resolve to absolute path


# rf_model = load(os.path.join(shared_data_path, 'random_forrest.pkl'))
# lgbm_model = load(os.path.join(shared_data_path, 'lightgbm.pkl'))
# xgboost_model = load(os.path.join(shared_data_path, 'xgboost.pkl'))


def get_rf_model():
    model = cache.get("rf_model")
    if model is None:
        model = load(os.path.join(shared_data_path, 'random_forrest.pkl'))
        cache.set("rf_model", model, timeout=None)  # Store indefinitely
    return model


def get_xgboost_model():
    model = cache.get("xg_boost")
    if model is None:
        model = load(os.path.join(shared_data_path, 'xgboost.pkl'))
        cache.set("xg_boost", model, timeout=None)  # Store indefinitely
    return model

def get_lightgbm_model():
    model = cache.get("lightgbm")
    if model is None:
        model = load(os.path.join(shared_data_path, 'lightgbm.pkl'))
        cache.set("lightgbm", model, timeout=None)  # Store indefinitely
    return model


def get_expected_columns():
    expected_columns = cache.get("expected_columns")
    if expected_columns is None:
        expected_columns = load(os.path.join(shared_data_path, 'expected_columns.pkl'))
        cache.set("expected_columns", expected_columns, timeout=None)  # Store indefinitely
    return expected_columns


# scaler = load(os.path.join(shared_data_path, 'scaler.pkl'))


def prepare_input(incoming_data: pd.DataFrame, expected_columns: list) -> pd.DataFrame:
    """One-hot encodes and aligns input data to match training features."""
    categorical_cols = ['district_name', 'foundation_name', 'layout_name', 'repair_name', 'wc_name', 'year_month']
    incoming_encoded = pd.get_dummies(incoming_data, columns=categorical_cols)
    # term = ['year_month_2025-04', 'year_month_2025-05', ]
    # expected_columns = [col for col in expected_columns if col not in term]

    # Add missing columns
    for col in expected_columns:
        if col not in incoming_encoded.columns:
            incoming_encoded[col] = 0

    # Drop any extra columns
    incoming_encoded = incoming_encoded[[col for col in expected_columns]]

    # Ensure correct column order
    incoming_encoded = incoming_encoded[expected_columns]

    # Force all columns to int (converts True/False to 1/0)
    incoming_encoded = incoming_encoded.astype(int)

    return incoming_encoded


def predict_with_confidence(model, X_row: pd.DataFrame) -> dict:
    """Generates prediction with a ± confidence interval using individual trees and histogram data."""
    booster = model.booster_
    all_preds = [booster.predict(X_row, num_iteration=tree_idx)[0] for tree_idx in range(booster.current_iteration())]

    mean_pred = np.mean(all_preds)
    std_pred = np.std(all_preds)
    # lower_bound = mean_pred - 1.96 * std_pred  # 95% CI approximation
    # upper_bound = mean_pred + 1.96 * std_pred
    # Generate histogram data
    counts, bin_edges = np.histogram(all_preds, bins='auto')  # You can also set bins=10 or another integer

    return {
        'prediction': mean_pred,
        'lower_bound': mean_pred - 1 * std_pred,
        'upper_bound': mean_pred + 1 * std_pred,
        'std_dev': std_pred,
        'histogram': {
            'counts': counts.tolist(),
            'bin_edges': bin_edges.tolist()
        }
    }


#
# def rf_model_prediction(incoming_features):
#     # New raw incoming data
#     incoming_data = pd.DataFrame(incoming_features)
#
#     # Preprocess and predict
#     processed_input = prepare_input(incoming_data, expected_columns).values
#     # scaled_input = scaler.transform(processed_input)
#     result = predict_with_confidence(rf_model, processed_input)
#
#     return result
# def rf_model_prediction(incoming_features):
#     print('FUNCTION WORKED')
#     incoming_data = pd.DataFrame(incoming_features)
#
#     # Load the latest cached model and expected columns
#     rf_model = get_rf_model()
#     print('MODEL LOADED WORKED')
#
#     expected_columns = get_expected_columns()
#     print('COLUMNS LOADED')
#
#
#     # Preprocess and predict
#     processed_input = prepare_input(incoming_data, expected_columns).values
#     result = predict_with_confidence(rf_model, processed_input)
#
#     return result
def rf_model_prediction(incoming_features):
    print('FUNCTION WORKED')
    incoming_data = pd.DataFrame(incoming_features)

    # Load the latest cached model and expected columns
    rf_model = get_lightgbm_model()
    print('MODEL LOADED WORKED')

    expected_columns = get_expected_columns()
    print('COLUMNS LOADED')

    # Preprocess and predict
    processed_input = prepare_input(incoming_data, expected_columns).values
    result = predict_with_confidence(rf_model, processed_input)

    return result
