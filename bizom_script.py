import os
import pandas as pd
import boto3
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Retrieve secrets from GitHub Actions environment variables
BIZOM_USERNAME = os.getenv("BIZOM_USERNAME")
BIZOM_PASSWORD = os.getenv("BIZOM_PASSWORD")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")

# Define the download directory
DOWNLOAD_DIR = "C:\\temp"  # Change this as needed, or use a default value
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Initialize WebDriver with download preferences
options = webdriver.ChromeOptions()
prefs = {"download.default_directory": DOWNLOAD_DIR}  # Ensure the correct variable name is used
options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(options=options)
driver.maximize_window()

def login():
    try:
        # Locate and input username and password
        username_field = driver.find_element(By.XPATH, "//input[@placeholder='Username']")
        password_field = driver.find_element(By.XPATH, "//input[@placeholder='Password']")
        username_field.send_keys(BIZOM_USERNAME)
        password_field.send_keys(BIZOM_PASSWORD)
        
        # Click login button
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "login"))
        )
        login_button.click()
        time.sleep(5)
        print("Logged in successfully!")
    except Exception as e:
        print("Login failed:", e)
        driver.quit()
        exit()

# Open the login page
driver.get("https://reports.bizom.in/users/login?redirect=%2Freports%2Fview%2F14085%3Furl%3Dreports%2Fview%2F14085")
login()

# Perform additional actions like updating and downloading
try:
    update_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "reportsUpdateButton"))
    )
    update_button.click()
    print("Update button clicked successfully!")
    time.sleep(5)

    dropdown = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "option-dropdown"))
    )
    dropdown.click()
    print("Dropdown clicked successfully!")

    download_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "downloadReportIcon"))
    )
    download_button.click()
    print("Download button clicked successfully!")
    time.sleep(20)
except Exception as e:
    print("An error occurred during download:", e)

# Detect and convert the downloaded file to CSV
def convert_to_csv(file_path):
    try:
        if file_path.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file_path)
        elif file_path.endswith((".txt", ".csv")):
            df = pd.read_csv(file_path, sep=None, engine="python")
        else:
            raise ValueError("Unsupported file format.")
        csv_file_path = file_path.rsplit(".", 1)[0] + ".csv"
        df.to_csv(csv_file_path, index=False)
        print(f"Converted to CSV: {csv_file_path}")
        return csv_file_path
    except Exception as e:
        print(f"Failed to convert file to CSV: {e}")
        return None

# Locate the latest downloaded file
downloaded_files = [os.path.join(DOWNLOAD_DIR, f) for f in os.listdir(DOWNLOAD_DIR) if os.path.isfile(os.path.join(DOWNLOAD_DIR, f))]
if downloaded_files:
    latest_file = max(downloaded_files, key=os.path.getctime)
    print(f"File downloaded: {latest_file}")
    latest_file = convert_to_csv(latest_file)  # Convert the file to CSV
else:
    print("No file downloaded.")
    latest_file = None

driver.quit()

# Upload the file to S3
def upload_to_s3(file_name, bucket_name, s3_key):
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY
        )
        with open(file_name, 'rb') as file_data:
            s3.upload_fileobj(file_data, bucket_name, s3_key)
        print(f"File uploaded to S3 bucket '{bucket_name}' with key '{s3_key}'.")
    except Exception as e:
        print("Failed to upload to S3:", e)

if latest_file:
    s3_key = f"{os.path.basename(latest_file)}"
    upload_to_s3(latest_file, BUCKET_NAME, s3_key)
else:
    print("No file to upload.")
