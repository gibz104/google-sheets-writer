from google_sheets_writer.writer import GoogleSheetsWriter

writer = GoogleSheetsWriter(
    auth_type='oauth',
)

writer.write_to_gsheets(
    workbook_name='my_workbook',
    data_lod=[
        {'Header 1': 1, 'Header 2': 2},
        {'Header 1': 1, 'Header 2': 2},
    ]
)
