import math
import pandas as pd
import numpy as np
import gspread
import logging

from typing import Optional, List, Literal
from google_sheets_writer.utils.other_utils import chunk_list
from functools import cached_property

# Gspread Documentation: https://docs.gspread.org/en/latest/oauth2.html
# Google Sheets API Limits: https://developers.google.com/sheets/api/limits
# Google Sheets Worksheet Size Limits: https://support.google.com/drive/answer/37603


class GoogleSheetsWriter:
    """
    This class is used to write data to Google Sheets. It will respect Google
    Sheet's worksheet size limits (10,000,000 cells) and will create new worksheets to
    accommodate larger datasets.
    """
    
    def __init__(
        self,
        user_email: Optional[str] = 'gibz@libertas.systems',  # all new workbooks will be shared with this email
        auth_type: Literal['oauth', 'service_account'] = 'oauth',  # authorization type
    ):
        self.user_email = user_email
        self.auth_type = auth_type

    @cached_property
    def gsheets_client(self):
        """
        Return a gspread client object.
        
        This is a cached property and will only be run once.  Subsequent calls will return the cached value.
        """
        if self.auth_type == 'oauth':
            return gspread.oauth()
        elif self.auth_type == 'service_account':
            return gspread.service_account()

    def get_last_cell(
        self,
        workbook_name: str,
        worksheet_name: str,
    ):
        """
        Given a workbook and worksheet name, return the cell address of the last cell in the worksheet.
        """

        wb = self.gsheets_client.open(workbook_name)
        ws = wb.worksheet(worksheet_name)
        last_row_num = len(ws.col_values(1))
        return f'A{last_row_num + 1}'

    def create_workbook(self, name: str):
        """
        Create a new workbook and share it with the provided user_email.  This is in case a service account was
        used and is the owner of the workbook.
        """

        wb = self.gsheets_client.create(name)
        wb.share(self.user_email, perm_type='user', role='writer')
        logging.info(f'Created "{name}" workbook.')

    def create_worksheet(self, workbook_name: str, worksheet_name: str, num_rows: int, num_cols: int):
        """
        Create a new worksheet in the provided workbook.  The worksheet will be created with
        the provided number of rows and columns.
        """

        wb = self.gsheets_client.open(workbook_name)
        wb.add_worksheet(worksheet_name, rows=num_rows, cols=num_cols)
        logging.info(f'Created "{worksheet_name}" worksheet in "{workbook_name}" workbook.')

    def delete_object(self, workbook_name: str, worksheet_name: Optional[str] = None):
        """
        Delete a worksheet or a workbook
        """

        wb = self.gsheets_client.open(workbook_name)
        if worksheet_name:
            wb.del_worksheet(wb.worksheet(worksheet_name))
        else:
            self.gsheets_client.del_spreadsheet(file_id=wb.id)

    def check_existence(
        self,
        workbook_name: str,
        worksheet_name: Optional[str] = None,
    ):
        """
        Returns a boolean indicating whether a workbook or worksheet exists.
        Providing a worksheet name is optional.
        """

        # Try opening worksheet, if one was provided
        if worksheet_name:
            try:
                workbook = self.gsheets_client.open(workbook_name)
                workbook.worksheet(worksheet_name)
                return True
            except gspread.exceptions.WorksheetNotFound:
                return False
            except gspread.exceptions.SpreadsheetNotFound:
                return False

        # Else try to just open workbook
        else:
            try:
                self.gsheets_client.open(workbook_name)
                return True
            except gspread.exceptions.SpreadsheetNotFound:
                return False

    def cleanup(
        self,
        max_objects: int,
        workbook_name: str,
        worksheet_name: Optional[str] = None,
    ):
        """
        Delete all worksheets or workbooks that are greater than or equal to the provided max_objects value.
        """

        _max_objects = max_objects

        while self.check_existence(
                workbook_name=workbook_name if worksheet_name else workbook_name + f'_{_max_objects}',
                worksheet_name=worksheet_name + f'_{_max_objects}' if worksheet_name else None,
        ):
            self.delete_object(
                workbook_name=workbook_name if worksheet_name else workbook_name + f'_{_max_objects}',
                worksheet_name=worksheet_name + f'_{_max_objects}' if worksheet_name else None,
            )
            _max_objects += 1

    def write_to_gsheets(
        self,
        data_lod,
        workbook_name: str,
        chunk_size: Optional[int] = 100_000,
        max_cells_per_sheet: Optional[int] = 2_500_000,
        max_cells_per_workbook: Optional[int] = 10_000_000,
    ):
        """
        Write a list of dicts to Google Sheets.  The max number of cells per sheet and workbook
        can also be provided.  If the data exceeds these limits, new workbooks will be created
        with the same name as the original workbook, but with a suffix of "_1", "_2", etc.

        As of 2/28/2023, Google Sheets only allows 10M "cells" per workbook.
        """

        n_records = len(data_lod)  # Get number of records
        n_cols = len(data_lod[0])  # Get number of columns
        total_cell_count = n_records * n_cols  # Calculate total number of cells
        number_of_workbooks = math.ceil(total_cell_count / max_cells_per_workbook)  # Number of workbooks needed
        number_of_worksheets = math.ceil(total_cell_count / max_cells_per_sheet)  # Number of worksheets needed
        worksheets_per_book = math.ceil(max_cells_per_workbook / max_cells_per_sheet)  # Worksheets per workbook
        rows_per_worksheet = math.ceil(max_cells_per_sheet / n_cols)  # Rows per worksheet

        # Get header names
        headers = [list(data_lod[0].keys())]

        cursor = 0  # Set cursor to 0
        current_worksheet = 0  # Set current worksheet counter to 0

        # Split data into multiple workbooks, if necessary
        for i in range(1, number_of_workbooks + 1):

            # Define dynamic workbook name
            _workbook_name = workbook_name + f'_{i}'

            logging.info(f'Starting write to "{_workbook_name}" workbook...')

            # Create workbook if it doesn't exist
            if not self.check_existence(workbook_name=_workbook_name):
                self.create_workbook(_workbook_name)
            
            # Open workbook
            workbook = self.gsheets_client.open(_workbook_name)

            sheets_written = 0  # Counter for how many sheets have been written to in this workbook
            records_written = 0  # Counter for how many records have been written to in this workbook

            # Split data into multiple worksheets, if necessary
            for j in range(1, worksheets_per_book + 1):
                if current_worksheet < number_of_worksheets:

                    # Define dynamic worksheet name
                    _worksheet_name = workbook_name + f'_{j}'

                    # Get number of records to write to worksheet
                    n_records_to_write = min(rows_per_worksheet, n_records - cursor)

                    # Resize sheet if it already exists
                    if self.check_existence(workbook_name=_workbook_name, worksheet_name=_worksheet_name):
                        worksheet = workbook.worksheet(_worksheet_name)
                        worksheet.clear()
                        worksheet.resize(rows=n_records_to_write, cols=n_cols)
                    # Else create the worksheet
                    else:
                        self.create_worksheet(
                            workbook_name=_workbook_name,
                            worksheet_name=_worksheet_name,
                            num_rows=n_records_to_write,
                            num_cols=n_cols,
                        )
                        worksheet = workbook.worksheet(_worksheet_name)

                    # Remove "Sheet1" sheet, if it exists
                    if self.check_existence(workbook_name=_workbook_name, worksheet_name="Sheet1"):
                        self.delete_object(workbook_name=_workbook_name, worksheet_name="Sheet1")

                    # Write headers to worksheet
                    worksheet.update('A1', headers)

                    # Chunk data and write to worksheet
                    worksheet_data = data_lod[cursor:cursor + n_records_to_write]
                    chunked_data_lod = chunk_list(worksheet_data, chunk_size=chunk_size)
                    for chunk in chunked_data_lod:
                        # Convert to pandas dataframe and handle NAs
                        df = pd.DataFrame(chunk, dtype='string')
                        df = df.fillna(np.nan).replace([np.nan], [None])

                        # Write data to next available row
                        worksheet.update(
                            self.get_last_cell(
                                workbook_name=_workbook_name,
                                worksheet_name=_worksheet_name,
                            ),
                            df.to_numpy().tolist(),
                        )

                    # Increment cursor and counters
                    cursor += n_records_to_write
                    records_written += n_records_to_write
                    sheets_written += 1

                # Increment current worksheet counter
                current_worksheet += 1

            logging.info(f'Wrote {records_written:,} records to "{_workbook_name}" in {sheets_written:,} sheets.')

            # Remove any extra worksheets from previous runs
            self.cleanup(
                workbook_name=_workbook_name,
                worksheet_name=workbook_name,
                max_objects=sheets_written + 1,
            )

        # Remove any extra workbooks from previous runs
        self.cleanup(
            workbook_name=workbook_name,
            max_objects=number_of_workbooks + 1,
        )
