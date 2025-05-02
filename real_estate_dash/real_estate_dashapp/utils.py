# from joblib import load
# import pandas as pd
# from django.conf import settings
# import os
# import numpy as np
#
# model_path = os.path.join(settings.BASE_DIR, 'ml_models')
#
# model = load(os.path.join(model_path, 'rf_model.pkl'))
# expected_columns = load(os.path.join(model_path, 'expected_columns.pkl'))
#
#
# def prepare_input(incoming_data: pd.DataFrame, expected_columns: list) -> pd.DataFrame:
#     """One-hot encodes and aligns input data to match training features."""
#     categorical_cols = ['district_name', 'foundation_name', 'layout_name', 'repair_name', 'wc_name', 'year_month']
#     incoming_encoded = pd.get_dummies(incoming_data, columns=categorical_cols)
#
#     # Add missing columns
#     for col in expected_columns:
#         if col not in incoming_encoded.columns:
#             incoming_encoded[col] = 0
#
#     # Drop any extra columns
#     incoming_encoded = incoming_encoded[[col for col in expected_columns]]
#
#     # Ensure correct column order
#     incoming_encoded = incoming_encoded[expected_columns]
#
#     # Force all columns to int (converts True/False to 1/0)
#     incoming_encoded = incoming_encoded.astype(int)
#
#     return incoming_encoded
#
#
# def predict_with_confidence(model, X_row: pd.DataFrame) -> dict:
#     """Generates prediction with a ± confidence interval using individual trees and histogram data."""
#     all_preds = [tree.predict(X_row)[0] for tree in model.estimators_]
#     mean_pred = sum(all_preds) / len(all_preds)
#     std_pred = pd.Series(all_preds).std()
#     print(std_pred)
#     # Generate histogram data
#     counts, bin_edges = np.histogram(all_preds, bins='auto')  # You can also set bins=10 or another integer
#
#     return {
#         'prediction': mean_pred,
#         'lower_bound': mean_pred - 2 * std_pred,
#         'upper_bound': mean_pred + 2 * std_pred,
#         'std_dev': std_pred,
#         'histogram': {
#             'counts': counts.tolist(),
#             'bin_edges': bin_edges.tolist()
#         }
#     }
#
#
# def rf_model_prediction(incoming_features):
#     # New raw incoming data
#     incoming_data = pd.DataFrame(incoming_features)
#
#     # Preprocess and predict
#     processed_input = prepare_input(incoming_data, expected_columns).values
#     result = predict_with_confidence(model, processed_input)
#
#     return result
