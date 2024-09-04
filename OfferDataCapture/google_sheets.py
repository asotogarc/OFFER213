from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.oauth2 import service_account
import pandas as pd
import config 

import numpy as np
from datetime import datetime, timedelta

def read_sheet(credentials):
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    SPREADSHEET_ID = '1PsSZJJtpcwSnfv7FMdsW1RqPO7JBV4izzB8klu0YzO4'

    creds = service_account.Credentials.from_service_account_info(credentials, scopes=SCOPES)

    service = build('sheets', 'v4', credentials=creds)

    sheet = service.spreadsheets()

    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range='Hoja 1').execute()

    values = result.get('values', [])

    if values:
        df = pd.DataFrame(values[1:], columns=values[0])
    else:
        df = pd.DataFrame()

    return df




def write_sheets(credentials, dataframe):
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    SPREADSHEET_ID = '1PsSZJJtpcwSnfv7FMdsW1RqPO7JBV4izzB8klu0YzO4'
    creds = service_account.Credentials.from_service_account_info(credentials, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    # Convert Timestamp objects to strings
    dataframe = dataframe.applymap(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if isinstance(x, pd.Timestamp) else x)
    # Convert the DataFrame to a list of lists, excluding the first row
    values = dataframe.iloc[1:].values.tolist()
    result = sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range='Hoja 1', 
        valueInputOption='USER_ENTERED',
        insertDataOption='INSERT_ROWS',
        body={'values': values}
    ).execute()
    return result
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# Crear datos de muestra
#num_rows = 10
#dates = [datetime.now() - timedelta(days=i) for i in range(num_rows)]
#names = ['Juan', 'María', 'Pedro', 'Ana', 'Luis']
#values = np.random.randint(1, 100, num_rows)

# Crear el DataFrame
#df = pd.DataFrame({
#    'Fecha': dates,
#    'Nombre': np.random.choice(names, num_rows),
#    'Valor': values
#})
#write_sheets(credentials=config.credentials, dataframe=df)
