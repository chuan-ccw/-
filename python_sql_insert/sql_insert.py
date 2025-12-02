import os
import csv

csv_folder_path = os.path.join("..", "database_data")
csv_names = [f for f in os.listdir(csv_folder_path) if f.endswith('.csv')]

with open("../sql/insert_db_values.sql", "w", encoding="utf-8-sig") as sql:
    sql.write("USE DrinkShopDB;\n")
    sql.write("GO\n")
    sql.write("\n")
    sql.write("DELETE FROM item;\n")
    sql.write("DELETE FROM [order];\n")
    sql.write("DELETE FROM product;\n")
    sql.write("DELETE FROM customer;\n")
    sql.write("DELETE FROM store;\n")
    sql.write("\n")
    
for file_name in csv_names:
    file_path = os.path.join(csv_folder_path, file_name)
    print(f"正在讀取: {file_name}")


    with open(file_path, "r", encoding='utf-8-sig') as f:

        reader = csv.reader(f)
        datalst = list(reader) 
        
        print(datalst)
        print("-" * 30) # 分隔線

        with open("../sql/insert_db_values.sql", "a", encoding="utf-8-sig") as sql:
            for line in datalst[1:]:
                tablename = file_name.rsplit(".")[0]
                values = "', '".join(line)              # 用單引號包起來
                query  = f"INSERT INTO {tablename} VALUES ('{values}');\n"
                sql.write(query)
            sql.write("\n")