import os
import pandas as pd
import boto3
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Specify download directory
download_dir = "\temp"
os.makedirs(download_dir, exist_ok=True)

# AWS credentials
AWS_ACCESS_KEY = "your_aws_access_key"
AWS_SECRET_KEY = "your_aws_secret_key"
BUCKET_NAME = "your_s3_bucket_name"

# Initialize WebDriver with headless settings
options = webdriver.ChromeOptions()
# Uncomment these for headless mode if necessary
# options.add_argument("--headless")
# options.add_argument("--no-sandbox")
# options.add_argument("--disable-dev-shm-usage")

# Set download preferences for Chrome
prefs = {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "directory_upgrade": True
}
options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(options=options)
driver.maximize_window()

def login():
    try:
        # Find the username and password fields and enter the credentials
        username_field = driver.find_element(By.XPATH, "//input[@placeholder='Username']")
        password_field = driver.find_element(By.XPATH, "//input[@placeholder='Password']")
        username_field.send_keys("Santosh.hr")
        password_field.send_keys("Swastiks@1")
        
        # Find and click the login button
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "login"))
        )
        login_button.click()
        
        # Wait for login to complete (you can adjust the time as needed)
        time.sleep(5)
        print("Logged in successfully!")
    except Exception as e:
        print("Login failed:", e)
        driver.quit()
        exit()

# Open the login page
driver.get("https://reports.bizom.in/users/login?redirect=%2Freports%2Fview%2F14085%3Furl%3Dreports%2Fview%2F14085")
login()
time.sleep(5)

# Clicking the Update Button
try:
    update_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "reportsUpdateButton"))
    )
    update_button.click()
    print("Update button clicked successfully!")
except Exception as e:
    print("Failed to click the Update button:", e)

time.sleep(5)

# Clicking the Download Dropdown
try:
    dropdown = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "option-dropdown"))
    )
    dropdown.click()
    print("Dropdown clicked successfully!")
except Exception as e:
    print("Failed to click the dropdown:", e)

# Clicking the Download Button
try:
    download_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "downloadReportIcon"))
    )
    download_button.click()
    print("Download button clicked successfully!")
except Exception as e:
    print("Failed to click the download button:", e)

# Wait time to allow the file to download
time.sleep(20)

# Detect and convert file to CSV
def convert_to_csv(file_path):
    try:
        print(f"Starting conversion for: {file_path}")
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

# Get the latest downloaded file
downloaded_files = [os.path.join(download_dir, f) for f in os.listdir(download_dir) if os.path.isfile(os.path.join(download_dir, f))]
if downloaded_files:
    latest_file = max(downloaded_files, key=os.path.getctime)
    print(f"File downloaded: {latest_file}")
    latest_file = convert_to_csv(latest_file)  # Convert the file to CSV
else:
    print("No file downloaded.")
    latest_file = None

driver.quit()

# Upload to S3 Function
def upload_to_s3(file_name, bucket_name, s3_key):
    try:
        # Use AWS credentials
        s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
        with open(file_name, 'rb') as file_data:
            s3.upload_fileobj(file_data, bucket_name, s3_key)
        print(f"File uploaded to S3 bucket '{bucket_name}' with key '{s3_key}'.")
    except Exception as e:
        print("Failed to upload to S3:", e)

# Upload the converted file to S3
if latest_file:
    s3_key = f"{os.path.basename(latest_file)}"
    upload_to_s3(latest_file, BUCKET_NAME, s3_key)
else:
    print("No file to upload.")
