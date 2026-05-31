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
    return response.json().get('files', [])

def get_airtable_records():
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Assets"
    headers = {'Authorization': f'Bearer {AIRTABLE_TOKEN}'}
    response = requests.get(url, headers=headers)
    records = response.json().get('records', [])
    return {r['fields'].get('File ID'): r['id'] for r in records if 'File ID' in r['fields']}

def upsert_file(file, existing_records):
    headers = {
        'Authorization': f'Bearer {AIRTABLE_TOKEN}',
        'Content-Type': 'application/json'
    }
    fields = {
        'File ID': file['id'],
        'Filename': file['name'],
        'File type': file['mimeType']
    }
    if file['id'] in existing_records:
        record_id = existing_records[file['id']]
        url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Assets/{record_id}"
        response = requests.patch(url, json={'fields': fields}, headers=headers)
        print(f"Updated: {file['name']} — status {response.status_code} — {response.text}")
    else:
        url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Assets"
        response = requests.post(url, json={'records': [{'fields': fields}]}, headers=headers)
        print(f"Created: {file['name']} — status {response.status_code} — {response.text}")

if __name__ == '__main__':
    print("Getting Google token...")
    token = get_google_token()
    print("Fetching files from Google Drive...")
    files = get_drive_files(token)
    print(f"Found {len(files)} files")
    print("Fetching existing Airtable records...")
    existing = get_airtable_records()
    print(f"Found {len(existing)} existing records")
    for file in files:
        upsert_file(file, existing)
    print(f"Done — processed {len(files)} files")
