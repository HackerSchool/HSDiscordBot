import logging
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

from cfg import MASTER_FOLDER_ID


def authenticate():
    gauth = GoogleAuth()

    if gauth.access_token_expired:
        logging.log(logging.INFO,"Access token expired. Renewing access token based on existing refresh token.")
        try:
            gauth.LoadCredentialsFile()
            gauth.Refresh()
            logging.log(logging.INFO, "Access token automatically renewed.")
        except:
            auth_url = gauth.GetAuthUrl()
            logging.log(logging.WARNING, f"Need new refresh token. Visit URL below, sign in to the bot's account, and input the code.\n{auth_url}")
            code = input("Code: ") # NOT GOOD, TEMPORARY FIX
            gauth.Auth(code)
        finally:
            gauth.SaveCredentialsFile()


    drive = GoogleDrive(gauth)
    return drive


def get_gdrive_folder_named(folder_name):
    """
    If a google drive folder with a given name exists in the bot's account, it is returned, otherwise return None
    """
    drive = authenticate()
    folders = drive.ListFile(
        {'q': f"mimeType='application/vnd.google-apps.folder' and '{MASTER_FOLDER_ID}' in parents and trashed=false"}).GetList()
    for folder in folders:
        if folder['title'].lower() == folder_name.lower():
            return folder
    return None

def create_gdrive_folder(folder_name):
    """
    Creates google drive foler with a given name, inside the master folder
    """
    drive = authenticate()
    folder = drive.CreateFile({'title' : folder_name, 'mimeType' : 'application/vnd.google-apps.folder', 'parents' : [{'id': MASTER_FOLDER_ID}]})
    folder.Upload()


def send_files(file_name, folder_name):
    """
    Sends file to google drive folder, assuming first two characters in file name are '.\'
    Returns: 
        -True if successful
        -False if unsuccessful
    """
    drive = authenticate()
    gfile = drive.CreateFile({'title': file_name})

    folders = drive.ListFile(
        {'q': "title='" + folder_name + "' and mimeType='application/vnd.google-apps.folder' and '{MASTER_FOLDER_ID}' in parents and trashed=false"}).GetList()
    for folder in folders:
        if folder['title'].lower() == folder_name.lower():
            
            gfile = drive.CreateFile({'title': file_name[2:], 'parents': [{'id': folder['id']}]})
            gfile.SetContentFile(file_name)
            gfile.Upload()
            return True
    return False
