import csv
from faker import Faker
import os

fake = Faker('zh_TW')
Faker.seed(33)

folder_path = '..\static\product_images'  # 資料夾路徑

# 定義您要的圖片副檔名
valid_extensions = ('.jpg', '.jpeg', '.png')

# 1. 取得資料夾內所有檔案
# 2. 透過列表生成式 (List Comprehension) 篩選結尾符合圖片格式的檔案
# f.lower() 是為了確保 .JPG (大寫) 也能被抓到
image_names = [f for f in os.listdir(folder_path) if f.lower().endswith(valid_extensions)]

# 輸出結果
print(image_names)

# 準備寫入的路徑
file_path = "../database_data/product.csv"

# 設定要產生的筆數
count = len(image_names)

with open(file_path, "w", newline='', encoding='utf-8-sig') as file:
    writer = csv.writer(file)

    # 寫入欄位名稱
    writer.writerow(["product_id", "name", "photo_url", "price"]) 

    i = 1   
    
    for names in image_names:
        product_name, price = names.rsplit(".")[0].split("_")

        writer.writerow([i, product_name, f"static/product_images/{product_name}_{price}.jpg", price])

        i += 1

print(f"成功產生 {count} 筆 50嵐 商品資料至 {file_path}")
