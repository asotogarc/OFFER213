from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.oauth2 import service_account



SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
KEY = 'key.json'

creds = None

creds = service_account.Credentials.from_service_account_file(KEY, scopes=SCOPES)

service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()


values = [['Otra prueba'],['Otra prueba2']]

result = sheet.values().append(spreadsheetId= SPREADSHEET_ID,
                             range='Hoja 1', 
                             valueInputOption='USER_ENTERED',
                             body={'values':values}).execute()




print(f'Datos insertados correctamente')