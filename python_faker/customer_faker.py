from faker import Faker
import csv

fake = Faker('zh_TW')
Faker.seed(33)

# 設定模板：09 開頭，後面接 8 個 # (代表隨機數字)
number_format = '09########' 

# 準備要寫入的檔案路徑 (注意：要包含檔名 .csv)
file_path = "database_data/customer.csv"

# 設定要產生的筆數
count = 20

# 開啟檔案 (使用 'w' 寫入模式)
with open(file_path, "w", newline='', encoding='utf-8-sig') as file:
    writer = csv.writer(file)

    # 寫入欄位名稱
    writer.writerow(["customer_id", "phone"])

    generated_phones = set() # 用來確保電話號碼不重複

    # 迴圈產生 20 筆
    for i in range(count):
        
        customer_phone = fake.numerify(text=number_format)

        while customer_phone in generated_phones:
            customer_phone = fake.numerify(text=number_format)
        
        generated_phones.add(customer_phone)

        writer.writerow([i+1, customer_phone])

print(f"成功產生 {count} 筆 電話資料至 {file_path}")