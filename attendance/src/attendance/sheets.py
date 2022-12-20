import os

from apiclient import discovery
from googleapiclient.errors import HttpError
from google.oauth2 import service_account


class GSheets:
    def __init__(self, credentials_file, scopes):
        """

        :param credentials_file:
            a json file
        """
        self.credentials = credentials_file
        self.scopes = scopes
        self._auth = self._read_credentials()

    def _read_credentials(self):
        """
        read the credentials
        :return:
        """
        print(f"Building credentials using {self.credentials}")
        secret_file = os.path.join(self.credentials)
        creds = service_account.Credentials.from_service_account_file(
            secret_file, scopes=self.scopes
        )
        return creds

    def get_sheets(self, sheet_id):
        """
        Get all sheets(tabs) from the Google Sheet
        :param sheet_id:
        :return:
        """
        print(f"Reading sheet={sheet_id}")
        if not self._auth:
            self._read_credentials()
        try:
            service = discovery.build('sheets', 'v4', credentials=self._auth)
            request = service.spreadsheets().get(
                spreadsheetId=sheet_id,
                includeGridData=False
            )
            response = request.execute()
            sheets = list(map(lambda a: a['properties']['title'], response['sheets']))
            return sheets
        except HttpError as err:
            print(err)

    def read_gsheet(
        self,
        sheet_id,
        tab_name,
        repeated_header="",
    ):
        """
        Read the specific tab from the google sheet
        read the first rows as header and map the remaining rows to the same

        :param sheet_id: gsheet id
        :param tab_name: gsheet tab name
        :param repeated_header: default 0
            if the same header is repeated add a counter to it
        :return:
        """
        data = []
        if not self._auth:
            self._read_credentials()
        try:
            service = discovery.build('sheets', 'v4', credentials=self._auth)
            request = service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=tab_name
            )
            response = request.execute()
            headers = response['values'][0]
            if repeated_header:
                counter = 0
                updated_headers = []
                for h in headers:
                    if h == repeated_header:
                        updated_headers.append(h + "." + str(counter))
                        counter += 1
                    else:
                        updated_headers.append(h)
                headers = updated_headers
            for val in response['values'][1:]:
                data.append(dict(zip(headers, val)))
            return data
        except HttpError as err:
            print(err)
            return []
