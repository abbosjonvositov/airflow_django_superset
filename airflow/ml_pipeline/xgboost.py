from xgboost import XGBRegressor
from ml_utils import preprocess_data, calculate_metrics
from itertools import product


def xgboost_tuning(X, y):
    X_train, X_test, y_train, y_test = preprocess_data(X, y)
    # {'n_estimators': 2000, 'max_depth': 9, 'learning_rate': 0.1, 'gamma': 0}

    param_grid = {
        'n_estimators': [1000],
        'max_depth': [9],
        'learning_rate': [0.1],
        'gamma': [0]
    }

    param_combinations = list(product(param_grid['n_estimators'], param_grid['max_depth'],
                                      param_grid['learning_rate'], param_grid['gamma']))
    total_iterations = len(param_combinations)

    best_params = {}
    best_score = float('-inf')
    best_model = None

    for iteration, (n_estimators, max_depth, learning_rate, gamma) in enumerate(param_combinations, start=1):
        print(f"Iteration {iteration}/{total_iterations}: n_estimators={n_estimators}, max_depth={max_depth}, "
              f"learning_rate={learning_rate}, gamma={gamma}")

        model = XGBRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            gamma=gamma,
            random_state=42
        )
        model.fit(X_train, y_train)
        score = model.score(X_test, y_test)

        if score > best_score:
            best_score = score
            best_model = model
            best_params = {
                'n_estimators': n_estimators,
                'max_depth': max_depth,
                'learning_rate': learning_rate,
                'gamma': gamma
            }

    y_pred = best_model.predict(X_test)
    return calculate_metrics(y_test, y_pred), best_model, best_params
