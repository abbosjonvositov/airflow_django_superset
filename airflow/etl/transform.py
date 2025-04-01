def clean_numbers(value):
    if isinstance(value, str):
        if value.endswith('+'):
            return int(value[:-1])  # Convert '6+' → 6
        if value.isdigit():
            return int(value)
    elif isinstance(value, (int, float)):
        return int(value)  # Convert float-like values safely
    return 0  # Return None for invalid values


mapping_dict_foundation = {
    "kirpich": "Кирпичный",
    "panel": "Панельный",
    "other": "Другие",
    "monolit": "Монолитный",
    "blok": "Блочный"
}

mapping_dict_repairs = {
    "evro": "Евроремонт",
    "custom": "Авторский проект",
    "sredniy": "Средний",
    "kapital": "Требует ремонта",
    "chernovaya": "Черновая отделка",
    "predchistovaya": "Предчистовая отделка"
}

mapping_dict_district = {
    "Мирабадский район": "Мирабадский район",
    "Яккасарайский район": "Яккасарайский район",
    "Мирзо-Улугбекский район": "Мирзо-Улугбекский район",
    "Юнусабадский район": "Юнусабадский район",
    "Яшнободский район": "Яшнабадский район",
    "Сергелийский район": "Сергелийский район",
    "Учтепинский район": "Учтепинский район",
    "Шайхантахурский район": "Шайхантахурский район",
    "Чиланзарский район": "Чиланзарский район",
    "Алмазарский район": "Алмазарский район",
    "Бектемирский район": "Бектемирский район",
}

mapping_dict_regions = {
    "город Ташкент": "toshkent-oblast",
    "Ташкентская область": "toshkent-oblast",
    "Самаркандская область": "samarkandskaya-oblast",
    "Навоийская область": "navoijskaya-oblast",
    "Джизакская область": "dzhizakskaya-oblast",
    "Бухарская область": "buharskaya-oblast",
    "Наманганская область": "namanganskaya-oblast",
    "Сурхандарьинская область": "surhandarinskaya-oblast",
    "Республика Каракалпакстан": "karakalpakstan",
    "Ферганская область": "ferganskaya-oblast",
    "Сырдарьинская область": "syrdarinskaya-oblast",
    "Кашкадарьинская область": "kashkadarinskaya-oblast",
    "Андижанская область": "andizhanskaya-oblast",
    "Хорезмская область": "horezmskaya-oblast",
}


def transform_data(ti):
    """
    Transform data pulled from XComs.
    """
    # Pull data from extract tasks using XComs
    olx_data = ti.xcom_pull(task_ids='extract_source_olx')  # Task ID for OLX
    uybor_data = ti.xcom_pull(task_ids='extract_source_uybor')  # Task ID for Uybor
    all_data = [
                   {**row, 'id': f"O{row['id']}"} for row in olx_data if 'id' in row
               ] + [
                   {**row, 'id': f"U{row['id']}"} for row in uybor_data if 'id' in row
               ]
    if not all_data:
        print("✅ No new data to insert.")
        return
    try:
        for index, row in enumerate(all_data):
            print(row)
            if 'id' not in row:
                print(f"❌ Error processing data: Missing 'id' in record {index + 1}")
                continue
            # Set default values for missing fields
            row = {
                key: (row.get(key, default_value) if row.get(key, default_value) is not None else default_value)
                for key, default_value in [
                    ('city_name', 'Unknown'),
                    ('region_name', 'Unknown'),
                    ('district_name', 'Unknown'),
                    ('latitude', 0),
                    ('longitude', 0),
                    ('total_area', 0),
                    ('number_of_rooms', 0),
                    ('floor', 0),
                    ('total_floors', 0),
                    ('price_per_sqm', 0),
                    ('price', 0),
                    ('id', 0),
                    ('last_refresh_time', 0),
                    ('layout_name', 'Unknown'),
                    ('foundation_name', 'Unknown'),
                    ('wc_name', 'Unknown'),
                    ('repair_name', 'Unknown'),
                    ('type_of_market_key', 'Unknown'),
                    ('is_furnished', 'Unknown'),
                    ('year_of_construction', 0),
                ]
            }

            row['number_of_rooms'] = clean_numbers(row.get('number_of_rooms'))
            row['total_area'] = clean_numbers(row.get('total_area'))
            row['floor'] = clean_numbers(row.get('floor'))
            row['total_floors'] = clean_numbers(row.get('total_floors'))
            row['price_per_sqm'] = clean_numbers(row.get('price_per_sqm'))
            row['price'] = clean_numbers(row.get('price'))

            row['district_name'] = mapping_dict_district.get(row['district_name'], row['district_name'])
            row['foundation_name'] = mapping_dict_foundation.get(row['foundation_name'], row['foundation_name'])
            row['repair_name'] = mapping_dict_repairs.get(row['repair_name'], row['repair_name'])
            row['region_name'] = mapping_dict_repairs.get(row['region_name'], row['region_name'])
        return all_data
    except Exception as e:
        raise RuntimeError(f"❌ Error transforming data: {e}")
