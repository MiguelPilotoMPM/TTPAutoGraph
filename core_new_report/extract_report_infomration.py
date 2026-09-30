import json
import re
from pathlib import Path
import fitz  # PyMuPDF


def extract_report(project_path: str, pdf_path: str) -> tuple[bool, dict, str]:
    """
    INPUTS:

        * Project Path: String
        * PDF Path: String

    OUTPUTS:

        * Is saved: Boolean (True if the report is saved, False otherwise)
        * Extracted CTI information: Dictionary
        * Path to the saved text file: String

    DEFINITION:

        1- Extract the text from the PDF report and save in a text file.
        2- Using regex.json read and use to extract CTI information and save it in a dictionary.
        3- Return True if the report is saved, False otherwise.
    """
    project = Path(project_path)
    pdf     = Path(pdf_path)

    # 1. Extract text from PDF and save to reports_txt/
    try:
        doc  = fitz.open(str(pdf))
        text = "\n".join(page.get_text() for page in doc)
        doc.close()

        txt_dir  = project / "reports_txt"
        txt_dir.mkdir(exist_ok=True)
        txt_path = txt_dir / f"{pdf.stem}.txt"
        txt_path.write_text(text, encoding="utf-8")
    except Exception:
        return False, {}, ""

    # 2. Load regex.json and extract CTI information
    # Expected format: { "category": [{"name": "...", "regex": "..."}, ...], ... }
    cti_info   = {}
    regex_file = project / "regex.json"
    if regex_file.exists():
        categories = json.loads(regex_file.read_text(encoding="utf-8"))
        for category, patterns in categories.items():
            cti_info[category] = {}
            for entry in patterns:
                matches = re.findall(entry["regex"], text, re.IGNORECASE)
                cti_info[category][entry["name"]] = list(set(matches)) if matches else []

    # 3. Return
    return True, cti_info, str(txt_path)