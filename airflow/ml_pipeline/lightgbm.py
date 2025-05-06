from lightgbm import LGBMRegressor
from ml_utils import preprocess_data, calculate_metrics
from itertools import product


def lightgbm_tuning(X, y):
    X_train, X_test, y_train, y_test = preprocess_data(X, y)

    # Define parameter grid
    param_grid = {
        'n_estimators': [1000],
        'max_depth': [None],
        'learning_rate': [None],
        'num_leaves': [1000]
    }

    # Compute total number of iterations
    param_combinations = list(product(param_grid['n_estimators'], param_grid['max_depth'],
                                      param_grid['learning_rate'], param_grid['num_leaves']))
    total_iterations = len(param_combinations)

    best_params = {}
    best_score = float('-inf')
    best_model = None

    for iteration, (n_estimators, max_depth, learning_rate, num_leaves) in enumerate(param_combinations, start=1):
        print(f"Iteration {iteration}/{total_iterations}: n_estimators={n_estimators}, max_depth={max_depth}, "
              f"learning_rate={learning_rate}, num_leaves={num_leaves}")

        model = LGBMRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            num_leaves=num_leaves,
            random_state=42
        )
        model.fit(X_train, y_train)
        score = model.score(X_test, y_test)  # Evaluate on test set

        if score > best_score:
            best_score = score
            best_model = model
            best_params = {
                'n_estimators': n_estimators,
                'max_depth': max_depth,
                'learning_rate': learning_rate,
                'num_leaves': num_leaves
            }

    y_pred = best_model.predict(X_test)
    return calculate_metrics(y_test, y_pred), best_model, best_params
