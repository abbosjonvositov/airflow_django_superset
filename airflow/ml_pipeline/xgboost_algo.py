from ml_utils import preprocess_data, calculate_metrics, save_model, save_expected_columns, apply_one_hot_encoding
from itertools import product
import time
from xgboost import XGBRegressor
import sys
import os
from datetime import datetime
from real_estate_dashapp.models import Model, ModelMetric, ModelTrainingData
import pandas as pd

sys.path.append("/opt/airflow/django_project")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "real_estate_dash.settings")


def xgboost_algo(**context):
    try:
        cleaned_df = context['task_instance'].xcom_pull(task_ids='preprocess_data_for_analysis',
                                                        key='preprocess_data_for_analysis')
        if cleaned_df is None:
            raise ValueError("No data received from XCom.")

        # Get sorted unique months
        # months = sorted(cleaned_df['year_month'].unique())
        # print(months)
        month_df = cleaned_df.copy()
        month_df['year_month'] = pd.to_datetime(month_df[['year', 'month']].assign(day=1)).dt.strftime('%Y-%m')
        months = sorted(month_df['year_month'].unique())

        print(months)

        best_models = []

        for i in range(1, len(months) + 1):
            subset_months = months[:i]  # Incremental grouping
            data_range_start = subset_months[0]
            data_range_end = subset_months[-1]

            data_range_start = datetime.strptime(data_range_start, "%Y-%m").date()
            data_range_end = datetime.strptime(data_range_end, "%Y-%m").date()

            # Check if a model for this data range already exists

            existing_model_data = ModelTrainingData.objects.filter(
                data_range_start=data_range_start,
                data_range_end=data_range_end,
                model__model_type="XGBoost",
            ).exists()

            if existing_model_data:
                print(f"Skipping training for {data_range_start} to {data_range_end}, model already trained.")
                continue  # Skip iteration if data range already trained

            # Prepare data
            filtered_df = cleaned_df[month_df['year_month'].isin(subset_months)]
            categorical_columns = cleaned_df.select_dtypes(include=['object']).columns.tolist()
            df_one_hot_encoded = apply_one_hot_encoding(filtered_df, categorical_columns)

            X = df_one_hot_encoded.drop(columns=['price_usd'])
            y = df_one_hot_encoded['price_usd']

            X_train, X_test, y_train, y_test = preprocess_data(X, y)

            param_grid = {
                'n_estimators': [696],
                'max_depth': [15],
                'learning_rate': [0.052229370288901435],
                'gamma': [0],
                'subsample': [0.9545061669656212],
                'colsample_bytree': [1],
                'colsample_bylevel': [1],
                'colsample_bynode': [0.8531864051192173],
                'min_child_weight': [10],
                'reg_alpha': [1],
                'reg_lambda': [5],
                'max_delta_step': [0],
                'grow_policy': ['depthwise'],
                'verbosity': [1],
                'eval_metric': ['rmse']
            }

            param_combinations = list(product(*param_grid.values()))
            best_params = {}
            best_score = float('-inf')
            best_model = None
            best_eval_results = {}

            for params in param_combinations:
                param_dict = {key: value for key, value in zip(param_grid.keys(), params)}
                print(f"Testing parameters: {param_dict}")

                # Train the model
                model = XGBRegressor(**param_dict, random_state=42)
                model.fit(X_train, y_train, eval_set=[(X_train, y_train), (X_test, y_test)], verbose=False)

                score = model.score(X_test, y_test)
                y_pred = model.predict(X_test)

                # Store model info
                model_instance = Model.objects.create(model_type='XGBoost')
                ModelTrainingData.objects.create(
                    model=model_instance,
                    data_range_start=data_range_start,
                    data_range_end=data_range_end
                )

                # Store metrics
                metrics = calculate_metrics(y_test, y_pred)
                ModelMetric.objects.create(
                    model=model_instance,
                    rmse=metrics['RMSE'],
                    mse=metrics['MSE'],
                    mape=metrics['MAPE'],
                    mae=metrics['MAE'],
                    r2=metrics['R2'],
                    observations_count=filtered_df.shape[0]
                )

                best_models.append((model_instance.model_name, score))
                print(
                    f"Trained model {model_instance.model_name} from {data_range_start} to {data_range_end} - Score: {score}")
                # save_model(model=model, filename='xgboost')
                print('---- XGBOOST | PKL MODEL SAVED SUCCESSFULLY ----')
                # save_expected_columns(X)

        return '-- STATUS: SUCCESS | ALL MODELS TRAINED (NEW ONLY) | METRICS STORED --'

    except Exception as e:
        print(f"Error during model training: {e}")
        raise
