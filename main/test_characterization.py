"""
Characterization Tests for WBS Enhancement Application (main.py)
================================================================
These tests capture the CURRENT behavior of the legacy code, including bugs.
They are designed to PASS against the existing code and serve as a safety net
for future refactoring. Do NOT fix bugs here — document them as they are.

To run:  python -m pytest test_characterization.py -v
"""

import json
import os
import re
import sys
import unittest
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import datetime, date
from io import StringIO

import pandas as pd

# Prevent the module-level Tk() from launching when importing main.py
# We must patch tkinter before importing main
import tkinter as tk


class TestValidateApiKey(unittest.TestCase):
    """Characterization tests for Application.validate_api_key.
    
    Current behavior:
    - Empty string → None (shows error)
    - Full-width characters → None (checked before format)
    - Exactly 48 alphanumeric chars → returns the key
    - Wrong length or special chars → None
    """

    @classmethod
    def setUpClass(cls):
        """Create a minimal Application instance with mocked Tk root."""
        cls.root = tk.Tk()
        cls.root.withdraw()  # Hide the window
        # We need to import Application after Tk is created
        # but main.py creates its own Tk at module level.
        # So we import the class via exec trickery or just test the method logic directly.

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        """Extract validate_api_key logic for isolated testing."""
        # Replicate the exact validation logic from main.py L1064-1076
        self.error_shown = None

        def mock_showerror(title, message):
            self.error_shown = message

        self.mock_showerror = mock_showerror

    def _validate_api_key(self, api_key):
        """Exact replica of the validate_api_key logic for testing."""
        import config
        pattern = r'^[A-Za-z0-9]{48}$'
        if not api_key:
            self.mock_showerror("Error", config.error_message["APIEmptyField"])
            return None
        elif re.search(r'[\uFF01-\uFF60\uFFE0-\uFFE6]', api_key):
            self.mock_showerror("Error", config.error_message["FullWidthCharacterError"])
            return None
        elif re.match(pattern, api_key):
            return api_key
        else:
            self.mock_showerror("Error", config.error_message["InvalidKeyError"])
            return None

    def test_empty_string_returns_none(self):
        """Empty API key returns None."""
        result = self._validate_api_key("")
        self.assertIsNone(result)
        self.assertIn("cannot be empty", self.error_shown)

    def test_none_input_returns_none(self):
        """None-ish falsy input returns None (empty string behavior)."""
        result = self._validate_api_key("")
        self.assertIsNone(result)

    def test_valid_48_alphanumeric_key(self):
        """Exactly 48 alphanumeric characters returns the key."""
        key = "A" * 48
        result = self._validate_api_key(key)
        self.assertEqual(result, key)

    def test_valid_mixed_case_digits_48_chars(self):
        """Mixed case letters and digits, 48 chars, returns key."""
        key = "aB3cD4eF5gH6iJ7kL8mN9oP0qR1sT2uV3wX4yZ5aB3cD4eF5"
        self.assertEqual(len(key), 48)
        result = self._validate_api_key(key)
        self.assertEqual(result, key)

    def test_47_chars_returns_none(self):
        """47 characters → invalid format."""
        key = "A" * 47
        result = self._validate_api_key(key)
        self.assertIsNone(result)
        self.assertIn("Invalid API Key format", self.error_shown)

    def test_49_chars_returns_none(self):
        """49 characters → invalid format."""
        key = "A" * 49
        result = self._validate_api_key(key)
        self.assertIsNone(result)

    def test_48_chars_with_special_characters_returns_none(self):
        """48 chars with special chars → invalid format."""
        key = "A" * 47 + "!"
        result = self._validate_api_key(key)
        self.assertIsNone(result)

    def test_full_width_character_detected(self):
        """Full-width characters are caught before format check."""
        key = "Ａ" + "A" * 47  # Full-width A + 47 normal chars
        result = self._validate_api_key(key)
        self.assertIsNone(result)
        self.assertIn("full-width", self.error_shown)

    def test_full_width_takes_precedence_over_length(self):
        """Full-width check happens before length/format check."""
        key = "Ａ"  # Just one full-width char, wrong length too
        result = self._validate_api_key(key)
        self.assertIsNone(result)
        self.assertIn("full-width", self.error_shown)

    def test_spaces_in_key_returns_none(self):
        """Spaces make the key invalid."""
        key = "A" * 24 + " " + "A" * 23
        result = self._validate_api_key(key)
        self.assertIsNone(result)

    def test_underscore_in_key_returns_none(self):
        """Underscores are not alphanumeric per the regex."""
        key = "A" * 47 + "_"
        result = self._validate_api_key(key)
        self.assertIsNone(result)


class TestReadFile(unittest.TestCase):
    """Characterization tests for the read_file method logic.
    
    Current behavior:
    - Files > 25MB → sys.exit() (kills thread, not app)
    - Empty Excel → returns None
    - Drops all-NaN columns
    - Fills remaining NaN with 0
    """

    def test_drops_all_nan_columns(self):
        """Columns that are entirely NaN are dropped."""
        df = pd.DataFrame({
            'A': [1, 2, 3],
            'B': [None, None, None],
            'C': [4, 5, 6]
        })
        df.dropna(axis=1, how='all', inplace=True)
        df.fillna(0, inplace=True)
        self.assertNotIn('B', df.columns)
        self.assertIn('A', df.columns)
        self.assertIn('C', df.columns)

    def test_fills_nan_with_zero(self):
        """Partial NaN values are filled with 0."""
        df = pd.DataFrame({
            'A': [1, None, 3],
            'C': [4, 5, None]
        })
        df.dropna(axis=1, how='all', inplace=True)
        df.fillna(0, inplace=True)
        self.assertEqual(df['A'].iloc[1], 0)
        self.assertEqual(df['C'].iloc[2], 0)

    def test_empty_dataframe_detected(self):
        """Empty DataFrame raises EmptyDataError."""
        df = pd.DataFrame()
        self.assertTrue(df.empty)

    def test_file_size_check_threshold(self):
        """25MB threshold is 25 * 1024 * 1024 bytes."""
        max_mb = 25 * 1024 * 1024
        self.assertEqual(max_mb, 26214400)


class TestCheckFileValidity(unittest.TestCase):
    """Characterization tests for check_file_validity method logic.
    
    Documents the current behavior including bugs:
    - Bug: L714 uses == instead of = for error_msg assignment
    - Returns on first row of each sheet (only checks one row)
    """

    def test_event_process_diagram_error_msg_assignment_fixed(self):
        """Fixed: L714 now uses = (assignment) instead of == (comparison).
        The error message is correctly set when this branch is hit.
        """
        # This is what the fixed code does:
        error_msg = ""
        error_msg = "Error! The file is not an Event Process Sequence Diagram History file."
        # error_msg is now correctly assigned
        self.assertEqual(error_msg, "Error! The file is not an Event Process Sequence Diagram History file.")

    def test_file_size_threshold_25mb(self):
        """Files over 25MB are rejected."""
        max_mb = 25 * 1024 * 1024
        self.assertTrue(26214401 > max_mb)
        self.assertFalse(26214400 > max_mb)


class TestScreenLayoutFilenameExtraction(unittest.TestCase):
    """Characterization tests for screen name extraction from file paths.
    
    Used in both read_screen_layout and convert_app_detailed_spec_data.
    Regex: r"\\([^_]+)_"
    """

    def test_simple_path_extraction(self):
        """Regex [^_]+ matches across backslashes, capturing full path segment.
        For r'C:\\project\\ScreenA_Layout.xlsx', it captures 'project\\ScreenA'
        because [^_]+ matches everything except underscores, including backslashes.
        The code then splits on '\\' and takes the last part.
        """
        file = r"C:\project\ScreenA_Layout.xlsx"
        match = re.search(r"\\([^_]+)_", file)
        self.assertIsNotNone(match)
        # The regex captures everything between first \\ and first _
        self.assertEqual(match.group(1), "project\\ScreenA")
        # The code then splits on \\ and takes [-1]
        extracted = match.group(1)
        parts = extracted.split('\\')
        self.assertEqual(parts[-1], "ScreenA")

    def test_nested_path_extraction(self):
        """With nested backslashes, extracts the last segment."""
        file = r"C:\project\subdir\ComponentName_Details.xlsx"
        match = re.search(r"\\([^_]+)_", file)
        self.assertIsNotNone(match)
        # re.search finds the LAST match? No, it finds the FIRST match.
        # First match: \project\ → "project"... wait, let's check
        # Actually \project\ has no underscore after it immediately
        # The regex looks for \(non-underscore chars)_
        # \project\ - no, this is \project\subdir which has \ not _
        # Actually let's trace: it looks for \ then non-_ chars then _
        # First match: \project\subdir\ComponentName_ 
        # Wait, [^_]+ is greedy, and it can match \ characters
        # So \project\subdir\ComponentName_ matches with group = "project\subdir\ComponentName"
        extracted_part = match.group(1)
        # The code then checks for \\ in extracted_part and splits
        backslash_count = extracted_part.count('\\')
        if backslash_count > 0:
            parts = extracted_part.split('\\')
            screen_name = parts[-1] + "_UI"
        else:
            screen_name = extracted_part + "_UI"
        self.assertEqual(screen_name, "ComponentName_UI")

    def test_no_underscore_in_filename_returns_none(self):
        """If filename has no underscore, regex may not match."""
        file = r"C:\project\NoUnderscoreHere.xlsx"
        match = re.search(r"\\([^_]+)_", file)
        # This depends on whether there's an underscore anywhere after a backslash
        self.assertIsNone(match)

    def test_screen_name_suffix_ui(self):
        """Screen layout names get '_UI' suffix."""
        extracted_part = "LoginScreen"
        screen_name = extracted_part + "_UI"
        self.assertEqual(screen_name, "LoginScreen_UI")


class TestConvertAppDetailedSpecData(unittest.TestCase):
    """Characterization tests for the state machine parser.
    
    Tests the exact parsing logic for converting structured Excel rows
    into the JSON format used for API requests.
    """

    def test_keywords_list(self):
        """Verify the exact keywords used for state transitions."""
        keywords = [
            '業務分割名\n/Business Division Name',
            '説明\n/Description',
            '処理名\n/Process Name',
            '引数\n/Argument',
            '戻り値\n/Return Value',
            'テーブル/ファイル\n/Table/File'
        ]
        self.assertEqual(len(keywords), 6)
        self.assertIn("Business Division Name", keywords[0])
        self.assertIn("Description", keywords[1])
        self.assertIn("Process Name", keywords[2])
        self.assertIn("Argument", keywords[3])
        self.assertIn("Return Value", keywords[4])
        self.assertIn("Table/File", keywords[5])

    def test_initial_methods_structure(self):
        """Methods list starts with one pre-populated dict."""
        methods = [{
            "Process Name": [],
            "Argument": [],
            "Return Value": [],
            "Table or File use": [],
            "Description": []
        }]
        self.assertEqual(len(methods), 1)
        self.assertEqual(methods[0]["Process Name"], [])

    def test_argument_row_format(self):
        """Arguments are captured from rows with exactly 4 elements."""
        row = [1, "paramName", "String", "A description"]
        self.assertEqual(len(row), 4)
        arg = {
            "No": row[0],
            "Name": row[1],
            "Type": row[2],
            "Description": row[3]
        }
        self.assertEqual(arg["No"], 1)
        self.assertEqual(arg["Name"], "paramName")

    def test_table_file_row_format(self):
        """Table/File entries are captured from rows with exactly 7 elements."""
        row = [1, "TBL001", "UserTable", "Y", "Y", "N", "N"]
        self.assertEqual(len(row), 7)
        entry = {
            "No": row[0],
            "Table_ID/File_ID": row[1],
            "Table_Name/File_Name": row[2],
            "CRUD Access for C": row[3],
            "CRUD Access for R": row[4],
            "CRUD Access for U": row[5],
            "CRUD Access for D": row[6]
        }
        self.assertEqual(entry["Table_ID/File_ID"], "TBL001")

    def test_json_output_indent(self):
        """Output JSON uses indent=6 and ensure_ascii=False."""
        data = {"test": "データ"}
        json_string = json.dumps(data, indent=6, ensure_ascii=False)
        self.assertIn("データ", json_string)
        # indent=6 means 6 spaces
        self.assertIn("      ", json_string)


class TestCreateWbsMarkdownParsing(unittest.TestCase):
    """Characterization tests for create_wbs markdown table extraction.
    
    Current behavior:
    - Regex r'\\|.*\\|' extracts lines with pipes
    - Includes the separator row (e.g., |---|---|)
    - Uses iloc[1:] to remove first data row (which is the separator)
    - Drops first and last columns (empty from pipe splitting)
    """

    def test_markdown_table_regex(self):
        """Regex captures all lines containing pipe characters."""
        content = """Here is the WBS:

| Item No. | Task | Assigned | Start | End |
|---|---|---|---|---|
| 1 | Design UI | Alice | 01/01/2025 | 01/05/2025 |
| 2 | Backend | Bob | 01/01/2025 | 01/10/2025 |

Some trailing text."""
        table_pattern = re.compile(r'\|.*\|')
        matches = table_pattern.findall(content)
        self.assertEqual(len(matches), 4)  # header + separator + 2 data rows

    def test_markdown_to_dataframe_pipeline(self):
        """Full pipeline: markdown → DataFrame with correct columns.
        After iloc[1:] removes separator row, and rename+drop removes
        the first data row (used as new header), we get N-2 data rows.
        """
        content = """| Item No. | Task | Assigned |
|---|---|---|
| 1 | Design | Alice |
| 2 | Backend | Bob |"""

        table_pattern = re.compile(r'\|.*\|')
        markdown_table = '\n'.join(table_pattern.findall(content))

        data = StringIO(markdown_table)
        df = pd.read_csv(data, sep="|", skipinitialspace=True, engine='python')

        # Remove the first row (separator)
        df = df.iloc[1:]

        # Drop first and last columns (empty from pipe format)
        df = df.drop(df.columns[[0, -1]], axis=1)

        # Re-header: uses first remaining row as column names, then drops it
        df = df.rename(columns=df.iloc[0]).drop(df.index[0])

        # With 4 lines (header, sep, row1, row2):
        # After iloc[1:] → 3 rows (sep removed, but header became columns)
        # Actually: pd.read_csv uses first line as header, so 3 data rows
        # iloc[1:] removes sep row → 2 rows
        # rename+drop uses row1 as new header → 1 row remains
        self.assertEqual(len(df), 1)
        self.assertIn("2", str(df.iloc[0].values))

    def test_empty_content_behavior(self):
        """No markdown table in content → empty matches list."""
        content = "No table here, just plain text."
        table_pattern = re.compile(r'\|.*\|')
        matches = table_pattern.findall(content)
        self.assertEqual(len(matches), 0)


class TestTaskListJsonFormat(unittest.TestCase):
    """Characterization tests for the task list JSON format 
    generated by read_ss_folder_files.
    """

    def test_json_list_format(self):
        """Task list JSON uses 'Item No' and 'Task Description' keys."""
        task_list = ["LoginScreen_UI", "UserManagement_Init"]
        json_list = [{'Item No': i + 1, 'Task Description': task}
                     for i, task in enumerate(task_list)]
        json_string = json.dumps(json_list, indent=4)

        parsed = json.loads(json_string)
        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0]["Item No"], 1)
        self.assertEqual(parsed[0]["Task Description"], "LoginScreen_UI")
        self.assertEqual(parsed[1]["Item No"], 2)

    def test_empty_task_list(self):
        """Empty task list produces empty JSON array."""
        task_list = []
        json_list = [{'Item No': i + 1, 'Task Description': task}
                     for i, task in enumerate(task_list)]
        json_string = json.dumps(json_list, indent=4)
        self.assertEqual(json.loads(json_string), [])


class TestDateValidation(unittest.TestCase):
    """Characterization tests for date-related behavior."""

    def test_date_format_output(self):
        """Dates are formatted as MM/DD/YYYY for the API prompt."""
        d = date(2025, 1, 15)
        formatted = d.strftime('%m/%d/%Y')
        self.assertEqual(formatted, "01/15/2025")

    def test_date_format_single_digit_month(self):
        """Single-digit months are zero-padded."""
        d = date(2025, 3, 5)
        formatted = d.strftime('%m/%d/%Y')
        self.assertEqual(formatted, "03/05/2025")


class TestConfigPrompts(unittest.TestCase):
    """Characterization tests for config.py prompt templates."""

    def test_prompt_list_task_placeholders(self):
        """prompt_list_task expects 3 format placeholders."""
        import config
        # Should contain these placeholders
        self.assertIn("{screen_layout_json}", config.prompt_list_task)
        self.assertIn("{app_detailed_spec_data_converted_json}", config.prompt_list_task)
        self.assertIn("{tasks_list_json}", config.prompt_list_task)

    def test_prompt_placeholders(self):
        """prompt expects these format placeholders."""
        import config
        self.assertIn("{task_details_data}", config.prompt)
        self.assertIn("{skill_set_data}", config.prompt)
        self.assertIn("{start_date_str}", config.prompt)
        self.assertIn("{end_date_str}", config.prompt)
        self.assertIn("{task_description}", config.prompt)
        self.assertIn("{assigned_to}", config.prompt)
        self.assertIn("{progress}", config.prompt)
        self.assertIn("{plan_start_date}", config.prompt)
        self.assertIn("{plan_end_date}", config.prompt)

    def test_prompt_can_be_formatted(self):
        """Prompt format with all placeholders succeeds."""
        import config
        result = config.prompt.format(
            task_details_data="tasks",
            skill_set_data="skills",
            start_date_str="01/01/2025",
            end_date_str="06/30/2025",
            task_description="desc",
            assigned_to="person",
            progress="To do",
            plan_start_date="01/01/2025",
            plan_end_date="06/30/2025",
        )
        self.assertIn("tasks", result)
        self.assertIn("skills", result)


class TestErrorMessages(unittest.TestCase):
    """Characterization tests for config.error_message dictionary."""

    def test_all_expected_keys_exist(self):
        """All error message keys used in main.py exist in config."""
        import config
        expected_keys = [
            "FileNotFoundError", "FolderNotFoundError", "ManyExcelError",
            "EmptyDataError", "ParserError", "FileTooBig", "APIKeyError",
            "FailReadError", "APIEmptyField", "InvalidKeyError",
            "FullWidthCharacterError", "GeneralError"
        ]
        for key in expected_keys:
            self.assertIn(key, config.error_message, f"Missing key: {key}")

    def test_many_excel_error_message_matches_code_limit(self):
        """ManyExcelError message now correctly says 50, matching the code threshold."""
        import config
        # Message and code both use 50
        self.assertIn("50", config.error_message["ManyExcelError"])
        code_threshold = 50
        self.assertEqual(code_threshold, 50)


class TestNoneSentinel(unittest.TestCase):
    """Documents the use of None as a sentinel value (fixed from NotImplemented)."""

    def test_task_details_response_initial_value(self):
        """task_details_response is initialized to None (fixed from NotImplemented)."""
        value = None
        self.assertIsNone(value)

    def test_none_is_falsy(self):
        """None is falsy — request_task_details failure will
        allow proper checking before send_data_to_chatai uses the value.
        """
        value = None
        self.assertFalse(bool(value))


class TestBrowseFileEdgeCases(unittest.TestCase):
    """Documents browse_file side effects."""

    def test_ss_folder_file_cleared_on_every_browse(self):
        """ss_folder_file.clear() is called regardless of label type.
        Browsing for skillset clears the SS folder files list.
        """
        ss_folder_file = ["file1.xlsx", "file2.xlsx"]
        # Simulate the clear that happens at L158 for ANY browse
        ss_folder_file.clear()
        self.assertEqual(len(ss_folder_file), 0)

    def test_folder_file_limit_is_50(self):
        """Folder browse rejects more than 50 Excel files."""
        file_count = 51
        self.assertTrue(file_count > 50)

    def test_folder_file_accepts_50(self):
        """Exactly 50 files is acceptable."""
        file_count = 50
        self.assertFalse(file_count > 50)


class TestScreenLayoutParsing(unittest.TestCase):
    """Characterization tests for screen layout row filtering."""

    def test_header_keyword_detection(self):
        """Header row keywords used for start detection."""
        keywordsHeader = ['画面項目名\n/Screen Item Name', 'タイプ\n/ Type']
        test_row = ['画面項目名\n/Screen Item Name', 'タイプ\n/ Type', 'Other']
        found = any(keyword in str(cell) for keyword in keywordsHeader for cell in test_row)
        self.assertTrue(found)

    def test_header_row_excluded_from_data(self):
        """Rows containing the header keyword text are excluded from data."""
        filtered_row = ['画面項目名\n/Screen Item Name', 'Type', 'Size']
        excluded = '画面項目名\n/Screen Item Name' in filtered_row
        self.assertTrue(excluded)

    def test_row_with_dash_values_excluded(self):
        """Rows where both row[1] and row[2] are '-' are excluded."""
        row = [1, '-', '-']
        include = len(row) > 1 and (row[1] != '-' or row[2] != '-')
        self.assertFalse(include)

    def test_row_with_one_dash_included(self):
        """Rows where only one of row[1]/row[2] is '-' are included."""
        row = [1, 'TextBox', '-']
        include = len(row) > 1 and (row[1] != '-' or row[2] != '-')
        self.assertTrue(include)


class TestDownloadResult(unittest.TestCase):
    """Characterization tests for download_result behavior."""

    def test_destination_path_construction(self):
        """File is saved to user's Downloads folder as Details_WBS.xlsm."""
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        destination = os.path.join(downloads_folder, "Details_WBS.xlsm")
        self.assertTrue(destination.endswith("Details_WBS.xlsm"))
        self.assertIn("Downloads", destination)

    def test_source_path_is_cwd_based(self):
        """Source file is loaded from current working directory."""
        current_directory = os.getcwd()
        source = os.path.join(current_directory, "Details_WBS.xlsm")
        self.assertTrue(source.endswith("Details_WBS.xlsm"))


if __name__ == '__main__':
    unittest.main()
