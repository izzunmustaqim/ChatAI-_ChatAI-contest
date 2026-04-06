# WBS Enhancement — ChatAI Contest APG

An AI-powered desktop application that automatically generates **Work Breakdown Structure (WBS)** documents from Fujitsu System Specification (SS) files. The tool parses screen layout and application detailed specification Excel files, sends them to the Fujitsu Gemini AI API for complexity analysis and task scheduling, and produces a professional WBS Excel output (`.xlsm`) with formatted timelines.

---

## ✨ Features

- **Automated SS Document Parsing** — Reads Screen Layout and Application Detailed Specification Excel files, extracting structured data (screen items, methods, arguments, CRUD tables)
- **AI-Powered Task Complexity Analysis** — Sends parsed data to Fujitsu's Gemini API to assess task complexity (Hard / Medium / Easy)
- **AI-Powered WBS Generation** — Generates a complete WBS with task assignments, start/end dates, and progress tracking based on team skillsets
- **Team Skillset Matching** — Reads a Members Skillset Excel file to optimally assign tasks based on seniority and skill levels
- **Excel Template Output** — Writes the WBS into a professionally formatted `.xlsm` template with VBA macro support
- **Simple GUI** — Tkinter-based desktop interface with file browsing, date pickers, and progress tracking

---

## 📁 Project Structure

```
ChatAI_contest/
├── main/
│   ├── main.py              # Entry point — launches the GUI
│   ├── app.py               # Application GUI (Tkinter widgets, orchestration)
│   ├── file_parser.py       # Pure file I/O: Excel parsing & validation
│   ├── api_client.py        # Fujitsu Gemini API communication
│   ├── wbs_writer.py        # WBS Excel generation (COM automation)
│   ├── config.py            # Prompt templates & error messages
│   └── test_characterization.py  # 49 characterization tests
├── JDU-WBS_Template_Samples.xlsm # WBS Excel template
├── azure-pipelines.yml      # CI/CD: Polaris security scanning
└── .gitignore
```

### Module Responsibilities

| Module | Purpose |
|--------|---------|
| `main.py` | Lightweight entry point — creates Tk root and starts the app |
| `app.py` | GUI layer — widgets, user interactions, pipeline orchestration |
| `file_parser.py` | Pure functions for reading, validating, and parsing Excel files |
| `api_client.py` | Single `send_gemini_request()` function for Gemini API calls |
| `wbs_writer.py` | Markdown-to-DataFrame conversion, Excel COM automation, download |
| `config.py` | AI prompt templates and user-facing error message strings |

---

## 🛠️ Prerequisites

- **OS**: Windows (required for Excel COM automation via `win32com`)
- **Python**: 3.10+
- **Fujitsu Gemini API Key**: 48-character alphanumeric key

### Python Dependencies

```
pandas
openpyxl
requests
pywin32
tkcalendar
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/izzunmustaqim/ChatAI-_ChatAI-contest.git
cd ChatAI-_ChatAI-contest
```

### 2. Install dependencies

```bash
pip install pandas openpyxl requests pywin32 tkcalendar
```

### 3. Run the application

```bash
cd main
python main.py
```

---

## 📋 How to Use

1. **Enter API Key** — Paste your 48-character Fujitsu Gemini API key
2. **Browse Members Skillset** — Select the `MEMBERS_SKILLSET.xlsx` file containing team member names, seniority levels, and skills
3. **Browse SS Documents Folder** — Select a folder containing:
   - `Screen Layout*.xlsx` — Screen layout specification files
   - `Application Detailed Specification*.xlsx` — App spec files
4. **Set Project Duration** — Pick start and end dates using the date pickers
5. **Click Start** — The app will:
   - Parse all SS documents
   - Send data to Gemini AI for complexity analysis
   - Send complexity + skills data for WBS generation
   - Write results to `Details_WBS.xlsm`
6. **Download WBS** — Click the download button to save the output to your Downloads folder

---

## 🔄 Application Flow

```
User Input (GUI)
    │
    ▼
┌─────────────┐     ┌──────────────────┐
│  app.py     │────▶│  file_parser.py  │  Parse Excel files
│  (GUI +     │     └──────────────────┘
│  orchestrate)│
│             │     ┌──────────────────┐
│             │────▶│  api_client.py   │  API Call #1: Get task complexity
│             │     └──────────────────┘
│             │     ┌──────────────────┐
│             │────▶│  api_client.py   │  API Call #2: Generate WBS
│             │     └──────────────────┘
│             │     ┌──────────────────┐
│             │────▶│  wbs_writer.py   │  Write Excel output
└─────────────┘     └──────────────────┘
    │
    ▼
Details_WBS.xlsm (output)
```

---

## 🧪 Testing

Run the characterization test suite (49 tests):

```bash
cd main
python -m pytest test_characterization.py -v
```

These tests document the application's current behavior and serve as a safety net for refactoring.

---

## 📄 Input File Formats

### Members Skillset (`MEMBERS_SKILLSET.xlsx`)

Excel file with team member information including:
- Member name
- Seniority level (Senior / Middle / Junior)
- Technical skills and proficiency levels

### Screen Layout Files (`Screen Layout*.xlsx`)

Fujitsu-format screen layout specs containing:
- Sheet: `項目定義` (Item Definition)
- Columns: Screen Item Name, Type

### Application Detailed Specification Files

Fujitsu-format app specs containing:
- Business Division Names
- Process Names, Arguments, Return Values
- Table/File CRUD access definitions
- Method descriptions

---

## ⚠️ Known Limitations

- **Windows-only** — Requires `win32com.client` for Excel COM automation
- **Requires Excel installed** — The WBS template uses VBA macros that run via Excel COM
- **Folder limit** — Maximum 50 Excel files per SS document folder
- **File size limit** — Individual files must be under 25MB

---

## 📜 License

This project was developed for the Fujitsu ChatAI Contest APG.
