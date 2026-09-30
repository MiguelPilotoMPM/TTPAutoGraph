import csv
from pathlib import Path
import fitz  # PyMuPDF
from langdetect import detect, LangDetectException

def is_duplicate(project_path: str, pdf_path: str, only_english: bool = True) -> int:
    """
    INPUTS:

        * Project Path: String
        * PDF Path: String
        * Only English Reports: Boolean (Default True, TTPxHunter only works with English reports)

    OUTPUT:

        * Is duplicate: Integer (1 if duplicate, 0 if not, 2 if non-English report but not duplicate)

    DEFINITION:

        1- Compare the name of the report with the rest of the PDF reports on the CSV pdf database.
        2- If only english, extract all the text form the PDF report and analyzes.
        3- Return 0 if the report is not a duplicate and is English.
        3- Return 1 if the report is a duplicate.
        3- Return 2 if the report is non-English but not a duplicate. 
    """
    project = Path(project_path)
    pdf     = Path(pdf_path)

    # 1. Check for duplicate name in reports.csv (the BBDD)
    existing_names = set()
    reports_csv = project / "reports.csv"
    if reports_csv.exists():
        with open(reports_csv, newline="", encoding="utf-8") as f:
            existing_names = {row[0] for row in csv.reader(f) if row}

    if pdf.stem in existing_names:
        return 1  # duplicate

    # 2. Language check (only if requested)
    if only_english:
        try:
            doc  = fitz.open(str(pdf))
            text = "".join(page.get_text() for page in doc[:5])[:2000].strip()
            doc.close()
            if not text or detect(text) != "en":
                return 2  # non-English report
        except LangDetectException:
            return 2  # non-English report

    return 0  # not a duplicate and is English