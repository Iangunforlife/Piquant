import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload


import zipfile

from zipfile import ZipFile
import time
import os
import io
from Google import Create_Service
from googleapiclient.http import MediaIoBaseDownload

import json



def Restore(id):
    CLIENT_SECRET_FILE = "credentials.json"
    API_NAME = "drive"
    API_VERSION = "V3"
    SCOPE = ['https://www.googleapis.com/auth/drive']

    service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPE)

    file_ids = [id]
    file_names = ["Piquant.backup.zip"]

    for file_id, file_name in zip(file_ids, file_names):
        request = service.files().get_media(fileId=file_id)

        fh = io.BytesIO()

        downloader = MediaIoBaseDownload(fd=fh, request=request)

        done = False

        while not done:
            status, done = downloader.next_chunk()
            print("Download process {0}".format(status.progress() * 100))

        fh.seek(0)

        with open(os.path.join("F:/Year 2/IT2656 Security Project/Piquant Integrated", file_name), "wb") as f:
            f.write(fh.read())
            f.close()

def unzip():
    # Create a ZipFile Object and load sample.zip in it
    with ZipFile('Piquant.backup.zip', 'r') as zipObj:
        # Extract all the contents of zip file in different directory
        zipObj.extractall('restored')


class MyDrive():
    def __init__(self):
        # If modifying these scopes, delete the file token.pickle.
        SCOPES = ['https://www.googleapis.com/auth/drive']
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('drive', 'v3', credentials=creds)

        # request a list of first N files or
        # folders with name and id from the API.
        #results = self.service.files().list(
            #pageSize=100, fields="files(id, name)").execute()
        #items = results.get('files', [])

        # print a list of files

        #print("Here's a list of files: \n")
        #print(*items, sep="\n", end="\n\n")

    def items(self):

        results = self.service.files().list(
            pageSize=100, fields="files(id, name)").execute()
        items = results.get('files', [])
        a_file = open("data.pkl", "wb")
        pickle.dump(items, a_file)
        a_file.close()

    def upload_file(self, filename, path):
        folder_id = "1h9jaTYpjZFi8Bk-ESl-NqI2zd81q_as8"
        media = MediaFileUpload(f"{path}{filename}")

        response = self.service.files().list(
                                        q=f"name='{filename}' and parents='{folder_id}'",
                                        spaces='drive',
                                        fields='nextPageToken, files(id, name)',
                                        pageToken=None).execute()
        if len(response['files']) == 0:
            file_metadata = {
                'name': filename,
                'parents': [folder_id]
            }
            file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            print(f"A new file was created {file.get('id')}")



        else:
            for file in response.get('files', []):
                # Process change

                update_file = self.service.files().update(
                    fileId=file.get('id'),
                    media_body=media,
                ).execute()
                print(f'Updated File ' + filename)


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))



def upload():
    zipf = zipfile.ZipFile('Piquant.backup.zip', 'w', zipfile.ZIP_DEFLATED)
    zipdir('F:/Year 2/IT2656 Security Project/Piquant Integrated', zipf) #need to change the path accordingly

    zipf.close()

    path = "F:/Year 2/IT2656 Security Project/Piquant Integrated"
    my_drive = MyDrive()
    my_drive.upload_file("/Piquant.backup.zip", path)


if __name__ == "__main__":
    while True:
        start = MyDrive()

        i = int(input("1 - Restore backup, 2- Upload zipped backup, 3- Exit.\nEnter option: "))

        if i == 1:
            id = input("Enter your file id: ")
            Restore(id)
            unzip()
            print("Restoration done on " + time.asctime(time.localtime(time.time())))
            print("\n")

        elif i == 2:
            upload()
            print("Upload done on " + time.asctime(time.localtime(time.time())))
            print("\n")

        else:
            break
