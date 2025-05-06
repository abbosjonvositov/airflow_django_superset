from ml_utils import (
    evaluate_selected_sequence,
    replace_unknown_with_nan,
    fill_missing_with_mode)
import numpy as np

repair_name_mapping = {
    'evro': 'Евроремонт',
    'sredniy': 'Средний',
    'chernovaya': 'Черновая отделка',
    'custom': 'Авторский проект',
    'kapital': 'Капитал'
}


def data_preprocess(**context):
    raw_data = context['task_instance'].xcom_pull(task_ids='extract_data_for_analysis', key='extract_data_for_analysis')
    categorical_columns = raw_data.select_dtypes(include=['object']).columns.tolist()
    numeric_columns = raw_data.select_dtypes(include=['float64', 'int64']).columns.tolist()
    replacements_drop_na_executed = replace_unknown_with_nan(raw_data, numeric_columns, categorical_columns)
    fill_missing_cat_vars = fill_missing_with_mode(replacements_drop_na_executed, categorical_columns)
    fill_missing_cat_vars['repair_name'] = fill_missing_cat_vars['repair_name'].replace(repair_name_mapping)
    fill_missing_cat_vars['is_primary'] = (fill_missing_cat_vars['type_of_market'] == 'primary').astype(int)
    cleaned_df = evaluate_selected_sequence(fill_missing_cat_vars, categorical_columns)
    context['task_instance'].xcom_push(key='preprocess_data_for_analysis', value=cleaned_df)
    return 'SUCCESS'
