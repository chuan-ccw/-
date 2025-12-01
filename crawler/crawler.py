import os
import time
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Selenium 相關模組
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def sanitize_filename(name):
    """
    將產品名稱轉換為合法的檔案名稱。
    移除或替換檔案系統不允許的字元 (如 /, \, :, *, ?, ", <, >, |)。
    """
    # 替換不合法字元為底線
    name = re.sub(r'[\\/*?:"<>|]', '_', name)
    # 移除前後空白
    return name.strip()

def download_image(url, folder, filename):
    """下載圖片並儲存"""
    try:
        response = requests.get(url, stream=True, timeout=10)
        if response.status_code == 200:
            # 判斷副檔名 (預設 jpg)
            ext = 'jpg'
            if '.png' in url: ext = 'png'
            elif '.jpeg' in url: ext = 'jpeg'
            elif '.webp' in url: ext = 'webp'
            
            full_path = os.path.join(folder, f"{filename}.{ext}")
            
            # 如果檔名重複，加上編號
            counter = 1
            while os.path.exists(full_path):
                full_path = os.path.join(folder, f"{filename}_{counter}.{ext}")
                counter += 1
            
            with open(full_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"[成功] 下載: {filename}")
        else:
            print(f"[失敗] 無法下載 (Status {response.status_code}): {url}")
    except Exception as e:
        print(f"[錯誤] 下載圖片時發生錯誤: {e}")

def main():
    target_url = "https://order.quickclick.cc/tw/food/P_kKKKKMjer/"
    
    # 使用相對路徑 (前提：必須在 crawler 資料夾內執行 python crawler.py)
    output_folder = "../static/product_images"

    # 建立輸出資料夾
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 設定 Selenium (使用無頭模式，即不顯示瀏覽器視窗，若想看過程可註解掉 '--headless')
    chrome_options = Options()
    # chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # 偽裝 User-Agent 以防被擋
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")

    print("啟動瀏覽器中...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        print(f"前往頁面: {target_url}")
        driver.get(target_url)
        
        # 等待初始載入
        time.sleep(5)

        # 模擬捲動頁面以觸發 Lazy Loading (圖片懶加載)
        print("捲動頁面載入所有內容...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            # 捲動到底部
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2) # 等待載入
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        # 解析 HTML
        print("解析頁面結構...")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        images = soup.find_all('img')
        download_count = 0
        
        print(f"找到 {len(images)} 個圖片標籤，開始過濾與下載...")

        for img in images:
            src = img.get('src')
            alt = img.get('alt')

            if not src or not alt:
                continue
                
            full_url = urljoin(target_url, src)

            skip_keywords = ['icon', 'logo', 'arrow', 'banner', 'loading', 'fb', 'line', 'instagram']
            if any(keyword in alt.lower() for keyword in skip_keywords):
                continue
            
            # --- 價格抓取邏輯 ---
            price = ""
            try:
                # 往上層找 3 層 parent
                parents = img.find_parents(limit=3)
                for parent in parents:
                    text = parent.get_text()
                    # 更新 Regex: 支援 $40, NT$40 等格式
                    price_match = re.search(r'(?:NT)?\$\s*(\d+)', text)
                    if price_match:
                        price = price_match.group(1)
                        break 
            except Exception as e:
                print(f"找價格時發生小錯誤: {e}")

            # 清理檔名
            safe_name = sanitize_filename(alt)
            
            # 如果有找到價格，加入檔名 (格式: 產品名_價格)
            if price:
                safe_name = f"{safe_name}_{price}"
            
            # 避免空檔名
            if not safe_name:
                continue

            print(f"發現產品: {safe_name} -> {full_url}")
            download_image(full_url, output_folder, safe_name)
            download_count += 1

        print(f"\n任務完成！共下載 {download_count} 張圖片，儲存於 '{output_folder}' 資料夾。")

    except Exception as e:
        print(f"發生錯誤: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()