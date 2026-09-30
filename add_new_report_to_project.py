import csv
import json
from pathlib import Path

from core_new_report.duplicate_lenguage_detect  import is_duplicate
from core_new_report.extract_report_infomration import extract_report
from core_new_report.ttpxhunter_function        import ttpxhunter


def add_new_report(project_path: str, pdf_path: str) -> bool: 
    """
    INPUTS:

        * Project Path: String
        * PDF Path: String

    OUTPUT:

        * Is ok: Boolean (True if the report was added successfully, False otherwise)

    DEFINITION:

        * If True, generate a text file with the extracted information
        * and create a new json file with the extracted CTI information
        * and TTPs in the reports processed database.

    """
    project = Path(project_path)
    pdf     = Path(pdf_path)

    try:
        # Load config
        config_file  = project / "config.json"
        config       = json.loads(config_file.read_text(encoding="utf-8")) if config_file.exists() else {}
        only_english = config.get("only_english", True)

        # 1. Duplicate / language check
        if is_duplicate(str(project), str(pdf), only_english):
            return False

        # 2. Extract text + CTI regex info
        saved, cti_info, txt_path = extract_report(str(project), str(pdf))
        if not saved:
            return False

        # 3. TTP extraction
        processed, ttp_info = ttpxhunter(txt_path)
        if not processed:
            return False

        # 4. Save merged result to reports_processed/
        result = {
            "file_name": pdf.name,
            "cti_info":  cti_info,
            "ttp_info":  ttp_info,
        }
        out_dir = project / "reports_processed"
        out_dir.mkdir(exist_ok=True)
        (out_dir / f"{pdf.stem}.json").write_text(
            json.dumps(result, indent=4, ensure_ascii=False), encoding="utf-8"
        )

        # 5. Register in reports.csv
        with open(project / "reports.csv", "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([pdf.stem, str(pdf)])

    except Exception:
        return False

    return True
