import gspread
from google_sheets_writer.writer import GoogleSheetsWriter
from unittest.mock import Mock, call, patch


@patch('google_sheets_writer.writer.gspread')
def test_writer_init(mock_gspread):
    # Test service account auth_type
    example_writer = GoogleSheetsWriter(
        user_email='test@test.com',
        auth_type='service_account',
    )
    assert example_writer.user_email == 'test@test.com'
    assert example_writer.auth_type == 'service_account'
    client = example_writer.gsheets_client
    assert client is not None

    # Test oauth auth_type
    example_writer = GoogleSheetsWriter(
        user_email='test@test.com',
        auth_type='oauth',
    )
    assert example_writer.user_email == 'test@test.com'
    assert example_writer.auth_type == 'oauth'
    client = example_writer.gsheets_client
    assert client is not None


@patch('google_sheets_writer.writer.gspread.oauth')
def test_get_last_cell(mock_client):
    example_data = ['Sample_Header', 'Sample_Data', 'Sample_Data']
    example_writer = GoogleSheetsWriter(
        user_email='test@test.com',
        auth_type='oauth',
    )

    # Test a worksheet with data
    mock_client().open().worksheet().col_values.return_value = example_data
    result = example_writer.get_last_cell(
        workbook_name='test_workbook',
        worksheet_name='test_worksheet',
    )
    assert result == 'A4'

    # Test a worksheet with no data
    mock_client().open().worksheet().col_values.return_value = []
    result = example_writer.get_last_cell(
        workbook_name='test_workbook',
        worksheet_name='test_worksheet',
    )
    assert result == 'A1'


@patch('google_sheets_writer.writer.gspread.oauth')
def test_create_workbook(mock_client):
    # Test appropriate calls are made for creating a workbook
    example_writer = GoogleSheetsWriter(
        user_email='test@test.com',
        auth_type='oauth',
    )
    example_writer.create_workbook('test_workbook')
    mock_client().create.assert_called_once_with('test_workbook')
    mock_client().create().share.assert_called_once_with('test@test.com', perm_type='user', role='writer')


@patch('google_sheets_writer.writer.gspread.oauth')
def test_create_worksheet(mock_client):
    # Test appropriate calls are made for creating a workbook
    example_writer = GoogleSheetsWriter(
        user_email='test@test.com',
        auth_type='oauth',
    )
    example_writer.create_worksheet(
        workbook_name='test_workbook',
        worksheet_name='test_worksheet',
        num_rows=100,
        num_cols=10,
    )
    mock_client().open.assert_called_once_with('test_workbook')
    mock_client().open().add_worksheet.assert_called_once_with('test_worksheet', cols=10, rows=100)


def test_delete_object():
    # Test 1: Delete a workbook
    with patch('google_sheets_writer.writer.gspread.oauth') as mock_client:
        mock_workbook = Mock()
        mock_workbook.id = 12345
        mock_client().open.return_value = mock_workbook
        example_writer = GoogleSheetsWriter(
            user_email='test@test.com',
            auth_type='oauth',
        )
        example_writer.delete_object(workbook_name='test_workbook')
        mock_client().open.assert_called_once_with('test_workbook')
        mock_client().del_spreadsheet.assert_called_once_with(file_id=12345)

    # Test 2: Delete a worksheet
    with patch('google_sheets_writer.writer.gspread.oauth') as mock_client:
        example_writer = GoogleSheetsWriter(
            user_email='test@test.com',
            auth_type='oauth',
        )
        example_writer.delete_object(workbook_name='test_workbook', worksheet_name='test_worksheet')
        mock_client().open.assert_called_once_with('test_workbook')
        mock_client().open().del_worksheet.assert_called_once_with(mock_client().open().worksheet('test_worksheet'))


def test_check_existence():
    # Test 1: Check existence of a worksheet
    with patch('google_sheets_writer.writer.gspread.oauth') as mock_client:
        example_writer = GoogleSheetsWriter(
            user_email='test@test.com',
            auth_type='oauth',
        )
        result = example_writer.check_existence(
            workbook_name='test_workbook',
            worksheet_name='test_worksheet',
        )
        mock_client().open.assert_called_once_with('test_workbook')
        mock_client().open().worksheet.assert_called_once_with('test_worksheet')
        assert result is True

    # Test 2: Check spreadsheet does not exist exception
    with patch('google_sheets_writer.writer.gspread.oauth') as mock_client:
        example_writer = GoogleSheetsWriter(
            user_email='test@test.com',
            auth_type='oauth',
        )
        mock_client().open.side_effect = gspread.exceptions.SpreadsheetNotFound
        result = example_writer.check_existence(
            workbook_name='test_workbook',
            worksheet_name='test_worksheet',
        )
        assert result is False

    # Test 3: Check worksheet does not exist exception
    with patch('google_sheets_writer.writer.gspread.oauth') as mock_client:
        example_writer = GoogleSheetsWriter(
            user_email='test@test.com',
            auth_type='oauth',
        )
        mock_client().open().worksheet.side_effect = gspread.exceptions.WorksheetNotFound
        result = example_writer.check_existence(
            workbook_name='test_workbook',
            worksheet_name='test_worksheet',
        )
        assert result is False

    # Test 4: Check existence of a workbook
    with patch('google_sheets_writer.writer.gspread.oauth') as mock_client:
        example_writer = GoogleSheetsWriter(
            user_email='test@test.com',
            auth_type='oauth',
        )
        result = example_writer.check_existence(
            workbook_name='test_workbook',
        )
        mock_client().open.assert_called_once_with('test_workbook')
        assert result is True

    # Test 5: Check spreadsheet does not exist exception
    with patch('google_sheets_writer.writer.gspread.oauth') as mock_client:
        example_writer = GoogleSheetsWriter(
            user_email='test@test.com',
            auth_type='oauth',
        )
        mock_client().open.side_effect = gspread.exceptions.SpreadsheetNotFound
        result = example_writer.check_existence(
            workbook_name='test_workbook',
        )
        assert result is False


@patch('google_sheets_writer.writer.GoogleSheetsWriter.check_existence')
def test_cleanup(mock_check_existence):
    # Test 1: Check that cleanup deletes worksheets
    with patch('google_sheets_writer.writer.gspread.oauth') as mock_client:
        example_writer = GoogleSheetsWriter(
            user_email='test@test.com',
            auth_type='oauth',
        )
        mock_check_existence.side_effect = [True, True, False]  # 2 extra worksheets
        example_writer.cleanup(
            max_objects=5,
            workbook_name='test_workbook',
            worksheet_name='test_worksheet',
        )
        calls = [
            call(mock_client().open().worksheet('test_worksheet_5')),
            call(mock_client().open().worksheet('test_worksheet_6'))
        ]
        mock_client().open().del_worksheet.assert_has_calls(calls)

    # Test 2: Check that cleanup deletes workbooks
    with patch('google_sheets_writer.writer.gspread.oauth') as mock_client:
        example_writer = GoogleSheetsWriter(
            user_email='test@test.com',
            auth_type='oauth',
        )
        mock_check_existence.side_effect = [True, True, False]  # 2 extra workbooks
        mock_wb_1 = Mock()
        mock_wb_1.id = 1234
        mock_wb_2 = Mock()
        mock_wb_2.id = 5678
        mock_client().open.side_effect = [mock_wb_1, mock_wb_2]

        example_writer.cleanup(
            max_objects=5,
            workbook_name='test_workbook',
        )

        calls = [
            call(file_id=1234),
            call(file_id=5678)
        ]
        mock_client().del_spreadsheet.assert_has_calls(calls)


@patch('google_sheets_writer.writer.GoogleSheetsWriter.cleanup')
@patch('google_sheets_writer.writer.GoogleSheetsWriter.get_last_cell')
@patch('google_sheets_writer.writer.GoogleSheetsWriter.check_existence')
def test_write_to_gsheets(mock_check_existence, mock_get_last_cell, mock_cleanup):
    example_data = [
        {'Header_1': 'test_data_1', 'Header_2': 'test_data_1'},
        {'Header_1': 'test_data_2', 'Header_2': 'test_data_2'},
        {'Header_1': 'test_data_3', 'Header_2': 'test_data_3'},
        {'Header_1': 'test_data_4', 'Header_2': 'test_data_4'},
        {'Header_1': 'test_data_5', 'Header_2': 'test_data_5'},
    ]

    # Normal test run (1 workbook, 1 worksheet)
    with patch('google_sheets_writer.writer.gspread.oauth') as mock_client:
        # mock_check_existence.side_effect = [True, True, True]
        mock_get_last_cell.return_value = 'A2'
        mock_check_existence.side_effect = [False, True, True, True]
        mock_cleanup.return_value = None
        mock_wb_1 = Mock()
        mock_wb_1.worksheet.return_value = Mock()
        mock_client().open.side_effect = mock_wb_1

        example_writer = GoogleSheetsWriter(
            user_email='test@test.com',
            auth_type='oauth',
        )
        example_writer.write_to_gsheets(
            data_lod=example_data,
            workbook_name='test_workbook',
        )
        calls = [
            call('A1', [['Header_1', 'Header_2']]),
            call(
                'A2',
                [
                    ['test_data_1', 'test_data_1'],
                    ['test_data_2', 'test_data_2'],
                    ['test_data_3', 'test_data_3'],
                    ['test_data_4', 'test_data_4'],
                    ['test_data_5', 'test_data_5'],
                ]
            )
        ]
        mock_client().open().worksheet().update.assert_has_calls(calls)

    # Test chunk sizes (chunk size of 2)
    with patch('google_sheets_writer.writer.gspread.oauth') as mock_client:
        # mock_check_existence.side_effect = [True, True, True]
        mock_get_last_cell.side_effect = ['A2', 'A4', 'A6']
        mock_check_existence.side_effect = [False, False, True, True]
        mock_cleanup.return_value = None
        mock_wb_1 = Mock()
        mock_wb_1.worksheet.return_value = Mock()
        mock_client().open.side_effect = mock_wb_1

        example_writer = GoogleSheetsWriter(
            user_email='test@test.com',
            auth_type='oauth',
        )
        example_writer.write_to_gsheets(
            data_lod=example_data,
            workbook_name='test_workbook',
            chunk_size=2,
        )
        calls = [
            call('A1', [['Header_1', 'Header_2']]),
            call(
                'A2',
                [
                    ['test_data_1', 'test_data_1'],
                    ['test_data_2', 'test_data_2'],
                ]
            ),
            call(
                'A4',
                [
                    ['test_data_3', 'test_data_3'],
                    ['test_data_4', 'test_data_4'],
                ]
            ),
            call(
                'A6',
                [
                    ['test_data_5', 'test_data_5'],
                ]
            )
        ]
        mock_client().open().worksheet().update.assert_has_calls(calls)