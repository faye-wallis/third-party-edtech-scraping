from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
import time, shutil
from dotenv import load_dotenv
import os
import pandas as pd
from datetime import datetime, timedelta

# load credentials from .env
load_dotenv()

#save some steps by opening directly to the Reports page
site_url = os.getenv('CAMPUS_SITE')
site_username = os.getenv('CAMPUS_USERNAME')
site_password = os.getenv('CAMPUS_PASSWORD')

#downloads/extract.py
download_path = os.getenv('CAMPUS_DOWNLOAD_PATH')
upload_path = os.getenv('CAMPUS_UPLOAD_PATH')

# define functions for easier iteration of common tasks
def enter_text(attribute, name, text):
    condition = wait.until(EC.presence_of_element_located((attribute, name)))
    element = driver.find_element(attribute, name)
    element.send_keys(text)

def click_button(attribute, name, list_index=None):
    if list_index == None:
        condition = wait.until(EC.presence_of_element_located((attribute, name)))
        element = driver.find_element(attribute, name)
        element.click()
    else:
        condition = wait.until(EC.presence_of_element_located((attribute, name)))
        element = driver.find_elements(attribute, name)[list_index]
        element.click() 

def select_option(attribute, name, option_num):
    condition = wait.until(EC.presence_of_element_located((attribute, name)))
    element = Select(driver.find_element(attribute, name))
    element.select_by_index(option_num)

def select_all(attribute, name):
    condition = wait.until(EC.presence_of_element_located((attribute, name)))
    element = Select(driver.find_element(attribute, name))
    for opt in element.options:
        element.select_by_visible_text(opt.get_attribute("innerText"))


s = Service(ChromeDriverManager().install())
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
driver = webdriver.Chrome(service=s, options=options)
wait = WebDriverWait(driver, 90)

#extract attendance report from infinite campus
driver.get(site_url)
enter_text("name", "username", site_username)
enter_text("name", "password", site_password)
click_button("id", "signinbtn")
time.sleep(10)
# there are a lot of nested iframes to navigate between
iframe1 = driver.find_element(By.ID, 'main-workspace')
driver.switch_to.frame(iframe1)
iframe2 = driver.find_element(By.ID, 'frameWorkspace')
driver.switch_to.frame(iframe2)
iframe3 = driver.find_element(By.ID, 'filterList')
driver.switch_to.frame(iframe3)
click_button("id", "button58")
click_button("id", "row227")
driver.switch_to.default_content()
driver.switch_to.frame(iframe1)
driver.switch_to.frame(iframe2)
# probably better to use one of selenium's built-in tools to time things out, but time.sleep saves you from needing to switch iframes all the time
time.sleep(5)
csv_option = driver.find_elements(By.ID, 'mode')[2]
time.sleep(5)
csv_option.click()
time.sleep(5)
click_button("id", "next")
time.sleep(10)
driver.quit()

#transform attendance report to reflect average attendance per site/day for the last month, then load results to OneDrive
filepath = r"C:\Users\FayeWallis\Downloads\extract.csv"
last_month = datetime.today() - timedelta(days=30)

df = pd.read_csv(filepath)
df['AttendanceUnit.date'] = pd.to_datetime(df['AttendanceUnit.date'])
df = df[df['AttendanceUnit.date'] > last_month]
df['present'] = 1
pivot_table_data = df.pivot_table(index='courseSection.courseName', columns='AttendanceUnit.date', values='present', aggfunc='sum')
df_pivot = pd.DataFrame(pivot_table_data)
df_pivot['Average Attendance'] = df_pivot.mean(axis=1)
df_pivot['Average Attendance'].to_excel(upload_path)
os.remove(filepath)