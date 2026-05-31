import os
import json
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

AIRTABLE_TOKEN = os.environ['AIRTABLE_TOKEN']
AIRTABLE_BASE_ID = os.environ['AIRTABLE_BASE_ID']
GOOGLE_DRIVE_FOLDER_ID = os.environ['GOOGLE_FOLDER_ID']
SERVICE_ACCOUNT_JSON = os.environ['GOOGLE_SERVICE_ACCOUNT_JSON']

def get_google_token():
    service_account_info = json.loads(SERVICE_ACCOUNT_JSON)
    credentials = service_account.Credentials.from_service_account_info(
        service_account_info,
        scopes=['https://www.googleapis.com/auth/drive.readonly']
    )
    credentials.refresh(Request())
    return credentials.token

def get_drive_files(token):
    url = "https://www.googleapis.com/drive/v3/files"
    params = {
        'q': f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents and trashed=false",
        'fields': 'files(id,name,mimeType)'
    }
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(url, params=params, headers=headers)
