import warnings
import requests
import json
import os

import time
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import imaplib
import email
from email.header import decode_header
import csvParser as cP
# Flowmon API credentials
USERNAME = 'USERNAME'
PASSWORD = 'PASSWORD'
BASE_URL = "URL"

GMAIL_IMAP_SERVER = "imap.gmail.com"
USERNAME = "USERNAME"
PASSWORD = "PASSWORD"
#SEARCH_SUBJECT = "TOP IPs ADS"
ATTACHMENT_FOLDER = "attachments"
def clean(text):
    # Clean text for creating a folder or saving a file
    return "".join(c if c.isalnum() else "_" for c in text)


# Connect to Gmail's IMAP server
# Connect to Gmail's IMAP server
def connect_to_gmail():
    mail = imaplib.IMAP4_SSL(GMAIL_IMAP_SERVER)
    mail.login(USERNAME, PASSWORD)
    return mail


# Function to search and retrieve only the latest email with a specific subject, including attachments
def fetch_latest_email_with_subject(subject):
    mail = connect_to_gmail()
    mail.select("inbox")  # Select the inbox folder

    # Search for emails with the specified subject
    status, messages = mail.search(None, f'SUBJECT "{subject}"')

    # Fetch the IDs of all matched emails
    email_ids = messages[0].split()
    if not email_ids:
        print("No emails found with the specified subject.")
        return None

    # Get only the latest email ID
    latest_email_id = email_ids[-1]

    # Fetch the latest email
    status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
    email_data = None
    filepath = None
    for response_part in msg_data:
        if isinstance(response_part, tuple):
            # Parse email bytes to message object
            msg = email.message_from_bytes(response_part[1])

            # Get the date the email was sent
            date_tuple = email.utils.parsedate_tz(msg["Date"])
            if date_tuple:
                local_date = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
                date_str = local_date.strftime("%Y-%m-%d %H:%M:%S")

            # Decode email subject
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding if encoding else "utf-8")

            # Get sender's email
            from_ = msg.get("From")

            # Initialize variables for body and attachments
            body = ""
            attachments = []

            # If the email message is multipart
            if msg.is_multipart():
                for part in msg.walk():
                    # Extract the email body
                    if part.get_content_type() == "text/plain" and part.get("Content-Disposition") is None:
                        try:
                            body = part.get_payload(decode=True).decode()
                        except Exception as e:
                            print(f"Error decoding email body: {e}")
                    # Handle CSV attachments
                    if part.get_content_disposition() == "attachment":
                        filename = part.get_filename()
                        if filename and filename.endswith(".csv"):
                            filename = clean(filename)
                            filepath = os.path.join(ATTACHMENT_FOLDER, filename)
                            with open(filepath, "wb") as f:
                                f.write(part.get_payload(decode=True))
                            attachments.append(filepath)
            else:
                # If email is not multipart, get the payload directly
                body = msg.get_payload(decode=True).decode()

            # Collect email data
            email_data = {
                "date": date_str,
                "subject": subject,
                "from": from_,
                "body": body,
                "attachments": attachments
            }

    # Logout and close connection
    mail.logout()
    return email_data, filepath


def get_latest_email(emails):
    current_date = time.strftime("%Y-%m-%d", time.localtime())
    for email in emails:
        pass
# Step 1: Obtain Access Token
def obtain_access_token():
    token_url = f"{BASE_URL}/resources/oauth/token"  # tu sa nevola /api kvoli niecomu.. :D
    payload = {
        'grant_type': 'password',
        'username': USERNAME,
        'password': PASSWORD,
        'client_id': 'invea-tech'
    }

    try:
        response = requests.post(token_url, data=payload, verify=False)
        response.raise_for_status()


        print(f"Raw response: {response.text}")
        json_result = json.loads(
            response.text)  # tu mame tokeny, toto returneme a pracujeme s tymto, ostatok kodu su sracky
        # Attempt to parse the JSON response
        return json_result['access_token'], json_result['refresh_token']
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
        print(f"Response content: {response.content}")  # Print content for debugging
        return None, None
    except json.JSONDecodeError:
        print("Failed to decode JSON response.")
        print(f"Response content: {response.content}")  # Print content for debugging
        return None, None


# Step 2: Retrieve Dashboard Content
def get_dashboard_content(access_token, dashboard_id):
    dashboard_url = f"{BASE_URL}/rest/fmd/overview/dashboards/{dashboard_id}"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(dashboard_url, headers=headers, verify=False)
        response.raise_for_status()
        dashboard_content = response.json()
        print("Dashboard Content retrieved successfully.")
        return dashboard_content
    except requests.exceptions.HTTPError as err:
        print(f"Failed to retrieve dashboard content: {err}")
        print(f"Response content: {response.content}")
        return None
    except json.JSONDecodeError:
        print("Failed to decode JSON response.")
        print(f"Response content: {response.content}")
        return None


def get_widget_data(access_token, widget_id):
    base_url = f"{BASE_URL}/rest/fmd/overview/widgets/{widget_id}"


    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    try:

        response = requests.get(base_url, headers=headers, verify=False)
        response.raise_for_status()


        widget_data = response.json()
        return widget_data

    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
        print(f"Response content: {response.content}")
        return None
    except requests.exceptions.RequestException as err:
        print(f"Request error: {err}")
        return None


def get_widgets_for_dashboard(access_token, dashboard_id):
    base_url = f"{BASE_URL}/rest/fmd/overview/widgets/find"


    params = {
        "search": f'{{"dashboard": "{dashboard_id}"}}'
    }


    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    try:

        response = requests.get(base_url, headers=headers, params=params, verify=False)
        response.raise_for_status()  # Raise an error for bad responses


        widget_data = response.json()
        return widget_data

    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
        print(f"Response content: {response.content}")
        return None
    except requests.exceptions.RequestException as err:
        print(f"Request error: {err}")
        return None


def get_report_data(access_token, report_name, file_type='csv', output_file=None):

    url = f"{BASE_URL}/ui/reports/generate?token={access_token}&type={file_type}&name={report_name.replace(' ', '%20')}"


    if not output_file:
        output_file = os.path.join(os.getcwd(), "reports", f"{report_name.replace(' ', '_')}.{file_type}")


    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    try:

        print(f"Downloading CSV from {url}...")
        response = requests.get(url, verify=False)
        response.raise_for_status()

        # Write the content to the output file
        with open(output_file, 'wb') as file:
            file.write(response.content)

        print(f"CSV downloaded successfully as {output_file}")
        return output_file
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while downloading the file: {e}")
        return False


def get_report_data_selenium(access_token, report_name, file_type='csv', output_file=None):

    url = f"{BASE_URL}/ui/reports/generate?token={access_token}&type={file_type}&name={report_name.replace(' ', '%20')}"


    if not output_file:
        output_file = os.path.join(os.getcwd(), "reports", f"{report_name.replace(' ', '_')}.{file_type}")


    os.makedirs(os.path.dirname(output_file), exist_ok=True)


    options = webdriver.ChromeOptions()
    download_dir = os.path.dirname(output_file)
    options.add_experimental_option("prefs", {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    options.add_argument("--ignore-certificate-errors")

    driver = webdriver.Chrome(options=options)

    try:

        driver.get(url)


        print("Waiting for the download button to appear...")
        download_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "qa-download"))
        )

        download_button.click()


        file_name = f"{report_name.replace(' ', '_')}.{file_type}"
        file_path = os.path.join(download_dir, file_name)

        print(f"Waiting for the report to download to {file_path}...")
        while not os.path.exists(file_path):
            time.sleep(1)

        print(f"Report downloaded successfully as {file_path}")
        return file_path

    except Exception as e:
        print(f"An error occurred while downloading the report: {e}")
        return False

    finally:

        driver.quit()


# Main execution
if __name__ == "__main__":

    latest_email, filepath = fetch_latest_email_with_subject("TOP IPs ADS")
    if latest_email:
        print("Date:", latest_email["date"])
        print("Subject:", latest_email["subject"])
        print("From:", latest_email["from"])
        print("Body:", latest_email["body"])
        if latest_email["attachments"]:
            print("Attachments:")
            for attachment in latest_email["attachments"]:
                print(f" - {attachment}")
        print("=" * 50)
    else:
        print("No latest email found with the specified subject.")

    if filepath:
        events = cP.parse_and_sum_events(filepath)
        print(events)

