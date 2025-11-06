from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time, requests, os, shutil, glob
import pandas as pd
from pathlib import Path
from datetime import datetime
from dateutil.relativedelta import relativedelta, FR, MO
import numpy as np
from dotenv import load_dotenv
from pathlib import Path

# load credentials and filepaths from .env
load_dotenv() 
site_username = os.getenv('STRIDE_USERNAME')
site_password = os.getenv('STRIDE_PASSWORD')
download_path = os.getenv('STRIDE_DOWNLOADS')
roster_path = os.getenv('ROSTER_PATH')
export_path = os.getenv('EXPORT_PATH')
assessment_path = Path("assessment_files")


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

#extract gap assessment reports from stride
#there's not a great way to select classes by name from the dropdown list, so it's easier to just iterate by number
classes = [1,2,3,6,7,14,15,16,17,18,20,21,22,23,24,25,26]
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
driver = webdriver.Chrome(ChromeDriverManager().install())
wait = WebDriverWait(driver, 90)
driver.get("https://www.stridelogin.com/login/talogin.php")
enter_text("name", "user_login", site_username)
enter_text("name", "password", site_password)
click_button("name", "login")
click_button("link text", "Reports")
for c in classes:
    click_button("link text", "Class Gap Report")
    select_option("name", "schoolid", c)
    click_button("link text", "Select All")
    click_button("class name", "css_button", -1)
    #stride reports take a while to load, and it's not always clear what to target in the tags
    #usually takes 30 seconds, but default to 40 just in case
    time.sleep(40)
    elements = driver.find_elements("class name", "export_csv")
    for element in elements:
        element.click()
    driver.back()
click_button("link text", "District Usage Report")
enter_text("name", "startdate", "10/13/2025")
enter_text("name", "enddate", "10/17/2025")
click_button("link text", "Select All")
click_button("class name", "css_button", -1)
time.sleep(5)
elements = driver.find_elements("class name", "export_csv")
for element in elements:
    element.click()
    time.sleep(5)

driver.quit()

#pull gap assessment files out of downloads folder
gap_text = 'class-gap' 
usage_text = 'district-summary' 
keeper_text = 'class-gap-ByStudent'

#not all of the gap assessment files are needed here
#sift out any files that are not organized by student
for filename in os.listdir(download_path):
    if gap_text in filename:
        source_path = os.path.join(download_path, filename)
        destination_path = os.path.join(assessment_path, filename)
        try:
            shutil.move(source_path, destination_path)
            print(f"Moved '{filename}' to '{assessment_path}'.")
        except Exception as e:
            print(f"Error moving '{filename}': {e}")
                  
for filename in os.listdir(assessment_path):
    file_path = os.path.join(assessment_path, filename)
    if keeper_text not in filename:
        os.remove(file_path)

#partition gap assessment files by subject
math_files = glob.glob(assessment_path+'/*Math*.csv')

ela_files = glob.glob(assessment_path+'/*Reading*.csv')

mth_list = []
ela_list = []

#transform math and ela assessment files into a more useable format
for f in ela_files:
    temp_df = pd.read_csv(f, skiprows=1).rename(
        columns={'Early Term (Prior Grade) Percent (%) Correct': 'ELA Early', 'Late Term (Current Grade) Percent (%) Correct': 'ELA Late'})
    ela_list.append(temp_df)

for f in math_files:
    temp_df = pd.read_csv(f, skiprows=1).rename(
        columns={'Early Term (Prior Grade) Percent (%) Correct': 'MTH Early', 'Late Term (Current Grade) Percent (%) Correct': 'MTH Late'})
    mth_list.append(temp_df)

#fill in school data by merging with roster file from OneDrive
df_mth = pd.concat(mth_list).drop('Mid Term (Current Grade) Percent (%) Correct', axis=1).rename(columns={'Early Term (Prior Grade) Percent (%) Correct': 'GAP Early', 'Late Term (Current Grade) Percent (%) Correct': 'GAP Late'})
df_ela = pd.concat(ela_list).drop('Mid Term (Current Grade) Percent (%) Correct', axis=1).rename(columns={'Early Term (Prior Grade) Percent (%) Correct': 'GAP Early', 'Late Term (Current Grade) Percent (%) Correct': 'GAP Late'})
df_sled = pd.read_excel(r"C:\Users\FayeWallis\Open Doors Academy\Data Manager - Documents\FY26\Enrollment\FY26 SLED.xlsx")
df_sled = df_sled[['Full Name', 'PBI Site']]

df_results = pd.merge(left=df_mth, right=df_ela, on='Student Name', how='outer')
df_results = pd.merge(left=df_results, right=df_sled, left_on='Student Name', right_on='Full Name', how='left').drop(columns=['Full Name'])

#final cleaning, then export results to OneDrive
for col in df_results.columns:
    nc = 'NC'
    df_results.loc[df_results[col].astype(str).str.contains(nc, na=False), col] = np.nan
site_groups = df_results.groupby('PBI Site').count()
site_group_df = pd.DataFrame(site_groups)
site_group_df = site_group_df.iloc[:, 1:5]
site_group_df.to_excel(export_path)

#clear out assessment folder before next run
for file in os.listdir(assessment_path):
    os.remove(os.path.join(assessment_path, file))