# <h1 align="center">google-sheets-writer</h1>

**This python class allows you to write any size data to Google Sheets by chunking data into multiple workbooks and worksheets.**

**Google Sheets has a limit of 10 million cells per workbook.**

[![Test Suite](https://github.com/gibz104/google-sheets-writer/actions/workflows/tests.yaml/badge.svg)](https://github.com/gibz104/google-sheets-writer/actions/workflows/tests.yaml)
[![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/gibz104/465cb74d7d8ba19a655fba50d0ce3665/raw/covbadge-google-sheets-writer.json)](https://github.com/gibz104/google-sheets-writer/actions/workflows/tests.yaml)
[![Py Versions](https://img.shields.io/badge/python-3.8_|_3.9_|_3.10-blue.svg)](https://www.python.org/downloads/)
[![Test OS](https://img.shields.io/badge/tested_on-ubuntu_|_mac_os-blue.svg)](https://github.com/gibz104/google-sheets-writer/actions/workflows/tests.yaml)

# Installation
This google sheets writer uses the gspread package (https://github.com/burnash/gspread), which itself uses the official Google Sheets API.  There are two methods to authenticate with Google Sheets and need to be setup prior to using this google sheets writer.  For either method chosen, you will need to create a local json file with your authentication details.

1) **Service Account**: authenticating on behalf of a bot (https://docs.gspread.org/en/latest/oauth2.html#for-bots-using-service-account)
2) **OAuth**: authenticating on behalf of an end user (https://docs.gspread.org/en/latest/oauth2.html#for-end-users-using-oauth-client-id)

Once done with the authentication steps outlined above in the gspread documentation, you are all set to begin using the google sheets writer. 

# Usage
#### Instantiate the `GoogleSheetsWriter` class with your chosen auth type:
OAuth:
```python
from google_sheets_writer.writer import GoogleSheetsWriter

writer = GoogleSheetsWriter(
    auth_type='oauth',
)
```
Service Account:
```python
from google_sheets_writer.writer import GoogleSheetsWriter

writer = GoogleSheetsWriter(
    auth_type='service_account',
)
```

---

#### Call the `write_to_gsheets` method with your data and the name for the workbook:
```python
writer.write_to_gsheets(
    workbook_name='my_workbook',
    data_lod=[
        {'Header 1': 1, 'Header 2': 2},
        {'Header 1': 1, 'Header 2': 2},
    ]
)
```
#### Additional parameters can also be provided:
 *  `chunk_size`: # of records to write at a time to Google Sheets (Default = 100,000)<br>
 *  `max_cells_per_sheet`: max # of cells per worksheet (Default = 3,000,000)<br>
 *  `max_cells_per_workbook`: max # of cells per workbook (Default = 9,000,000)<br>

# Tests
Basic unittests are in place in the `/tests` directory which can be run locally using `pytest`.  There is also a github workflow associated with this repo that will run the tests and report the code coverage on every push (https://github.com/gibz104/google-sheets-writer/actions/workflows/tests.yaml).

Tests have been run on python versions 3.8, 3.9, and 3.10 on both Ubuntu and Mac OS.  Testing status and coverage are reported as badges at the top of this readme.

# Disclaimer
Google Sheets currently limits a workbook to a max of 10,000,000 cells per workbook.  You may recieve errors when setting the `max_cells_per_workbook` parameter close to the 10,000,000 limit.

