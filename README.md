# MKC Attendance Automation

### Pre-requisite
1. Google Service Account
   1. [Create a Google Service account and download credentials as JSON](https://robocorp.com/docs/development-guide/google-sheets/interacting-with-google-sheets#create-a-google-service-account)
2. Attendance Google Sheet Id 
3. Sign up at [Nylas](https://dashboard.nylas.com/)
   1. Connect your gmail account:
   2. Quickstart -> Connect an email account -> Use my own account 
   3. Copy CLIENT_ID, CLIENT_SECRET and ACCESS_TOKEN 

### Create a config file
 - Create a copy of [config-template.ini](bin/config-template.ini) as "config.ini"
 - In "config.ini", set the following:
   - credentials_file=<path of json file downloaded in #1i>
   - attendance_sheet_id=<From #2>
   - to_emails=<comma separated emails>
   - client_id, client_secret and access_token from #3iii

### Setup an environment
 - `make python-build`
 
### How to execute
 - `python bin/main.py --config <path-of-config.ini>`
