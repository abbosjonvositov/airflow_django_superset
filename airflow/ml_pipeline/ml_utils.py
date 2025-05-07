import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib
import os
import json
from joblib import dump


def test_dir_save():
    scaler_path = os.path.join("/shared_data", "pkls", "data_test.json")
    data = {
        'name': 'Abbos',
        'surname': 'Vositov'
    }
    with open(scaler_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def preprocess_data(X, y):
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)
    scaler_path = os.path.join("/shared_data", "pkls", "scaler.pkl")
    joblib.dump(scaler, scaler_path)

    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=23)
    return X_train, X_test, y_train, y_test


# Function to calculate metrics
def calculate_metrics(y_test, y_pred):
    rmse = (mean_squared_error(y_test, y_pred)) ** 0.5
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
    r2 = r2_score(y_test, y_pred)
    return {
        "RMSE": rmse,
        "MAE": mae,
        "MSE": mse,
        "MAPE": mape,
        "R2": r2
    }


def apply_one_hot_encoding(df, categorical_columns):
    df_encoded = pd.get_dummies(df, columns=categorical_columns)
    for col in df_encoded.select_dtypes(include=['bool']).columns:
        df_encoded[col] = df_encoded[col].astype(int)
    return df_encoded


def eliminate_outliers_quantile_clipping(df, column, lower_quantile=0.01, upper_quantile=0.99):
    lower_bound = df[column].quantile(lower_quantile)
    upper_bound = df[column].quantile(upper_quantile)
    return df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]


def evaluate_selected_sequence(df, categorical_columns):
    # Columns to clean and corresponding methods
    cleaning_sequence = [
        ('total_area', 'Quantile Clipping', eliminate_outliers_quantile_clipping),
        ('price_usd', 'Quantile Clipping', eliminate_outliers_quantile_clipping)
    ]

    # Start with the original DataFrame
    processed_df = df.copy()

    # Apply the selected methods in sequence to the corresponding columns
    for column, method_name, method in cleaning_sequence:
        try:
            processed_df = method(processed_df, column)
        except Exception as e:
            print(f"Error applying method {method_name} to column {column}: {e}")
            continue  # Skip this column if there's an error

    # Apply one-hot encoding for categorical columns
    # processed_df = apply_one_hot_encoding(processed_df, categorical_columns)

    return processed_df


def replace_unknown_with_nan(raw_data, numeric_columns, categorical_columns):
    columns_to_replace_unknown = categorical_columns
    raw_data.loc[:, columns_to_replace_unknown] = raw_data[columns_to_replace_unknown].replace('Unknown', np.nan)

    columns_to_check = numeric_columns

    raw_data.loc[:, columns_to_check] = raw_data[columns_to_check].apply(lambda x: np.where(x <= 0, np.nan, x))
    tashkent_df = raw_data.dropna(subset=['price_usd', 'floors', 'number_of_rooms', 'total_area'])
    return tashkent_df


def fill_missing_with_mode(df, columns, group_by='district_name'):
    for column in columns:
        # Get mode for each district
        mode_values = df.groupby(group_by)[column].agg(lambda x: x.mode()[0] if not x.mode().empty else None)

        # Get the global mode for the entire dataset in case some districts have no mode
        global_mode = df[column].mode()[0] if not df[column].mode().empty else None

        # Fill missing values for each district with the district mode, or fallback to global mode
        df.loc[:, column] = df.apply(
            lambda row: (
                mode_values[row[group_by]] if pd.isna(row[column]) and mode_values[row[group_by]] is not None
                else (global_mode if pd.isna(row[column]) else row[column])
            ),
            axis=1
        )

    return df


def save_model(model, filename):
    scaler_path = os.path.join("/shared_data", "pkls", f'{filename}.pkl')
    dump(model, scaler_path)
    print(f"Model saved as {filename}.pkl")
    print(f"Expected columns saved as {filename}_columns.pkl")


def save_expected_columns(X):
    expected_columns = list(X.columns)
    scaler_path = os.path.join("/shared_data", "pkls", f'expected_columns.pkl')
    dump(expected_columns, scaler_path)
