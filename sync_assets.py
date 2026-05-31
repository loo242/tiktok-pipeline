import os
import requests

GOOGLE_DRIVE_FOLDER_ID = os.environ['GOOGLE_FOLDER_ID']
AIRTABLE_TOKEN = os.environ['AIRTABLE_TOKEN']
AIRTABLE_BASE_ID = os.environ['AIRTABLE_BASE_ID']
GOOGLE_TOKEN = os.environ['GOOGLE_TOKEN']

def get_drive_files():
    url = f"https://www.googleapis.com/drive/v3/files"
    params = {
        'q': f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents and trashed=false",
        'fields': 'files(id,name,mimeType)'
    }
    headers = {'Authorization': f'Bearer {GOOGLE_TOKEN}'}
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
        requests.patch(url, json={'fields': fields}, headers=headers)
        print(f"Updated: {file['name']}")
    else:
        url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Assets"
        requests.post(url, json={'records': [{'fields': fields}]}, headers=headers)
        print(f"Created: {file['name']}")

if __name__ == '__main__':
    files = get_drive_files()
    existing = get_airtable_records()
    for file in files:
        upsert_file(file, existing)
    print(f"Done — processed {len(files)} files")
