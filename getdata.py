import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import time
driver = webdriver.Chrome() 
url="https://m.imdb.com/user/ur171015315/watchlist/?ref_=nv_usr_wl"
driver.get(url)
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36"}
last_height = driver.execute_script("return document.body.scrollHeight")
while True:
    # 捲動到底部
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)  # 等待頁面加載

    # 取得新的頁面高度，判斷是否載入了新內容
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break  # 若頁面高度未變化，表示沒有更多資料
    last_height = new_height

# 取得頁面內容
soup = BeautifulSoup(driver.page_source, "html.parser")
driver.quit()  # 結束 WebDriver
series = soup.find_all("div",class_="sc-5bc66c50-0 bZBaVw")
intro = soup.find_all("div",class_="ipc-html-content-inner-div")
aintro=[]
count=0
for i in intro:
    temp = i.get_text(strip=True)
    aintro.append(temp)
for i in series:
    title = i.find('h3').get_text(strip=True)
    try:
        score = i.find('span',class_="ipc-rating-star--rating").get_text(strip=True)
    except:
        score = "None"
    print(f"{title}")
    print(f"★ {score}")
    print(aintro[count])
    print("-" * 40)
    count+=1