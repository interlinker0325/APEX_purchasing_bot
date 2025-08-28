from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, json
import pyautogui

cService = webdriver.ChromeService()

driver = webdriver.Chrome(service=cService)
driver.set_window_size(1200, 750)
driver.set_window_position(140, 20)

driver.get('https://dashboard.apextraderfunding.com/member/')
time.sleep(5)

# current_position = pyautogui.position()
# print(f"Current mouse position: x={current_position.x}, y={current_position.y}")

x, y = 896, 891
pyautogui.moveTo(x, y, duration=0.3)
pyautogui.click()
time.sleep(1)

user_name = driver.find_element(By.ID, "amember-login")
user_name.send_keys("tran325")
pwd = driver.find_element(By.ID, "amember-pass")
pwd.send_keys("Pwd123!@#")
time.sleep(10)

