import csv
from faker import Faker

fake = Faker('zh_TW')
Faker.seed(33)

# 準備寫入的路徑
file_path = "database_data/store.csv"

# 設定要產生的筆數
count = 20

with open(file_path, "w", newline='', encoding='utf-8-sig') as file:
    writer = csv.writer(file)
    
    # 寫入欄位名稱
    writer.writerow(['store_id', 'name'])
    
    generated_ids = set() # 用來確保統編不重複
    generated_names = set() # 用來確保店名不重複

    for i in range(count):
        
        tax_id = fake.numerify("########")
        store_name = fake.city_name()

        # 簡單的防重複機制
        while tax_id in generated_ids:
            tax_id = fake.numerify("########")
    
        while store_name in generated_ids:
            store_name = fake.city_name()
        
        generated_ids.add(tax_id)
        generated_names.add(store_name)

        # 2. 產生分店名稱 行政區店 (如：信義區店)
        store_name = f"50嵐 {store_name}店"

        # 寫入 CSV
        writer.writerow([tax_id, store_name])

print(f"成功產生 {count} 筆 50嵐 分店資料至 {file_path}")