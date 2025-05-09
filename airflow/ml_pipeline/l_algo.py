from ml_utils import preprocess_data, calculate_metrics, save_model, save_expected_columns, apply_one_hot_encoding
from itertools import product
import time
from lightgbm import LGBMRegressor
import sys
import os

from datetime import datetime
from real_estate_dashapp.models import Model, ModelMetric, ModelTrainingData

sys.path.append("/opt/airflow/django_project")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "real_estate_dash.settings")


def lightgbm_algorithm(**context):
    try:
        cleaned_df = context['task_instance'].xcom_pull(task_ids='preprocess_data_for_analysis',
                                                        key='preprocess_data_for_analysis')
        if cleaned_df is None:
            raise ValueError("No data received from XCom.")

        # Get sorted unique months
        months = sorted(cleaned_df['year_month'].unique())
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
                model__model_type="LightGBM",
            ).exists()

            if existing_model_data:
                print(f"Skipping training for {data_range_start} to {data_range_end}, model already trained.")
                continue  # Skip iteration if data range already trained

            # Prepare data
            filtered_df = cleaned_df[cleaned_df['year_month'].isin(subset_months)]
            categorical_columns = cleaned_df.select_dtypes(include=['object']).columns.tolist()
            df_one_hot_encoded = apply_one_hot_encoding(filtered_df, categorical_columns)

            X = df_one_hot_encoded.drop(columns=['price_usd'])
            y = df_one_hot_encoded['price_usd']

            print(X.columns)

            X_train, X_test, y_train, y_test = preprocess_data(X, y)

            param_grid = {
                'n_estimators': [1000],
                'learning_rate': [None],
                'max_depth': [None],
                'num_leaves': [1000],
                'min_child_samples': [10],
                'min_child_weight': [1e-3],
                'subsample': [0.8],
                'colsample_bytree': [1.0],
                'reg_alpha': [0.0],
                'reg_lambda': [0.3],
                'early_stopping_rounds': [10],
                'random_state': [23]
            }

            param_combinations = list(product(
                param_grid['n_estimators'], param_grid['learning_rate'], param_grid['max_depth'],
                param_grid['num_leaves'], param_grid['min_child_samples'], param_grid['min_child_weight'],
                param_grid['subsample'], param_grid['colsample_bytree'], param_grid['reg_alpha'],
                param_grid['reg_lambda'], param_grid['early_stopping_rounds']
            ))
            total_iterations = len(param_combinations)

            for iteration, params in enumerate(param_combinations, start=1):
                (n_estimators, learning_rate, max_depth, num_leaves, min_child_samples, min_child_weight,
                 subsample, colsample_bytree, reg_alpha, reg_lambda, early_stopping_rounds_value) = params

                print(f"Iteration {iteration}/{total_iterations}: {params}")

                model = LGBMRegressor(
                    n_estimators=n_estimators,
                    learning_rate=learning_rate,
                    max_depth=max_depth,
                    num_leaves=num_leaves,
                    min_child_samples=min_child_samples,
                    min_child_weight=min_child_weight,
                    subsample=subsample,
                    colsample_bytree=colsample_bytree,
                    reg_alpha=reg_alpha,
                    reg_lambda=reg_lambda,
                    early_stopping_rounds=early_stopping_rounds_value,
                    random_state=23,
                    force_col_wise=True,
                )
                model.fit(
                    X_train, y_train,
                    eval_set=[(X_test, y_test)],
                    eval_metric="mse",
                )
                score = model.score(X_test, y_test)  # Evaluate on test set
                y_pred = model.predict(X_test)

                # Store model info
                model_instance = Model.objects.create(model_type='LightGBM')
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
                save_model(model=model, filename='lightgbm')
                save_expected_columns(X)
                print('---- LIGHTGBM | PKL MODEL SAVED SUCCESSFULLY ----')

        return '-- STATUS: SUCCESS | ALL MODELS TRAINED (NEW ONLY) | METRICS STORED --'

    except Exception as e:
        print(f"Error during model training: {e}")
        raise
