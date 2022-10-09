# MKC Attendance Automation

### Pre-requisite
 - Google Service Account
 - [Create a Google Service account and download credentials as JSON](https://robocorp.com/docs/development-guide/google-sheets/interacting-with-google-sheets#create-a-google-service-account)
 - Attendance Google Sheet Id
 - Student Master Sheet Id

### Create a config file
 - Create a copy of [config-template.ini](bin/config-template.ini) as "config.ini"
 - Set service account json path to "credentials_file" 
 - Update the Google Sheet Ids and to_email

### Setup an environment
 - `make python-build`
 
### How to execute
 - `python bin/main.py --config <path-of-config.ini>`
