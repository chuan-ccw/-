import os
import csv
import re

csv_folder_path = os.path.join("..", "database_data")
csv_names = [f for f in os.listdir(csv_folder_path) if f.endswith('.csv')]

def has_chinese(s):
    return bool(re.search(r'[\u4e00-\u9fff]', s))

with open("../sql/insert_db_values.sql", "w", encoding="utf-8-sig") as sql:
    sql.write("USE DrinkShopDB;\nGO\n\n")
    sql.write("DELETE FROM item;\n")
    sql.write("DELETE FROM [order];\n")
    sql.write("DELETE FROM product;\n")
    sql.write("DELETE FROM customer;\n")
    sql.write("DELETE FROM store;\n\n")

for file_name in csv_names:
    file_path = os.path.join(csv_folder_path, file_name)
    print(f"正在讀取: {file_name}")

    with open(file_path, "r", encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        datalst = list(reader)

        with open("../sql/insert_db_values.sql", "a", encoding="utf-8-sig") as sql:
            tablename = file_name.rsplit(".", 1)[0]

            for line in datalst[1:]:
                formatted_values = []
                for value in line:
                    if has_chinese(value):
                        formatted_values.append(f"N'{value}'")   # 中文 → N'中文字'
                    else:
                        formatted_values.append(f"'{value}'")    # 英文數字 → 'value'

                values_str = ", ".join(formatted_values)
                query = f"INSERT INTO {tablename} VALUES ({values_str});\n"
                sql.write(query)

            sql.write("\n")
