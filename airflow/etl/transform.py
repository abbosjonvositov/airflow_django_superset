from utils import XComDataWrapper


def transform_data(ti):
    """
    Transform data pulled from XComs.
    """
    # Pull data from extract tasks using XComs
    extracted_data_olx = ti.xcom_pull(task_ids='extract_source_olx')  # Task ID for OLX
    extracted_data_uybor = ti.xcom_pull(task_ids='extract_source_uybor')  # Task ID for Uybor

    print("Transforming data...")
    print(f"Extracted OLX Data: {len(extracted_data_olx)}")
    print(f"Extracted Uybor Data: {len(extracted_data_uybor)}")

    # Add your transformation logic here
    transformed_data = {
        "olx_transformed": extracted_data_olx,
        "uybor_transformed": extracted_data_uybor
    }

    print(f"Transformed Data: {len(transformed_data)}")
    return transformed_data
