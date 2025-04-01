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
            row = {key: (value if value is not None else default_value) for key, value, default_value in [
                ('city_name', row.get('city_name', 'Unknown'), 'Unknown'),
                ('region_name', row.get('region_name', 'Unknown'), 'Unknown'),
                ('district_name', row.get('district_name', 'Unknown'), 'Unknown'),
                ('latitude', row.get('latitude', 0), 0),
                ('longitude', row.get('longitude', 0), 0),
                ('total_area', row.get('total_area', 0), 0),
                ('number_of_rooms', row.get('number_of_rooms', 0), 0),
                ('floor', row.get('floor', 0), 0),
                ('total_floors', row.get('total_floors', 0), 0),
                ('price_per_sqm', row.get('price_per_sqm', 0), 0),
                ('price', row.get('price', 0), 0),
                ('id', row.get('id', 0), 0),
                ('last_refresh_time', row.get('last_refresh_time', 0), 0),
                ('layout_name', row.get('layout_name', 'Unknown'), 'Unknown'),
                ('foundation_name', row.get('foundation_name', 'Unknown'), 'Unknown'),
                ('wc_name', row.get('wc_name', 'Unknown'), 'Unknown'),
                ('repair_name', row.get('repair_name', 'Unknown'), 'Unknown'),
                ('type_of_market_key', row.get('type_of_market_key', 'Unknown'), 'Unknown'),
                ('is_furnished', row.get('is_furnished', 'Unknown'), 'Unknown'),
                ('year_of_construction', row.get('year_of_construction', 0), 0),
            ]}
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

