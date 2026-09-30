import os
import json
import csv
from pathlib import Path

def create_project(project_data):
    """
    Create the project structure:
    - Main folder: project name (without extension)
    - Inside: name.project file with the absolute path
    - Subfolders: reports_processed, reports_pdf, reports_txt
    - Files: config.json, regex.json, reports.csv
    """
    base_path = Path(project_data["path"]).resolve()
    if not base_path.exists():
        raise ValueError(f"La ruta base no existe: {base_path}")
    if not os.access(base_path, os.W_OK):
        raise ValueError(f"No hay permisos de escritura en: {base_path}")

    # Main folder = project name (without .project)
    project_folder = base_path / project_data["name"]
    if project_folder.exists():
        raise FileExistsError(f"El proyecto ya existe en: {project_folder}")

    # Create main folder
    os.makedirs(project_folder)

    # Create .project file with the path
    project_file = project_folder / f"{project_data['name']}.project"
    with open(project_file, "w", encoding="utf-8") as f:
        f.write(str(project_folder.resolve()))

    # Create subfolders
    os.makedirs(project_folder / "reports_processed")
    os.makedirs(project_folder / "reports_pdf")
    os.makedirs(project_folder / "reports_txt")

    # config.json (according to specification)
    config = {
        "project_name": project_data["name"],
        "project_path": str(project_folder.resolve()),
        "description": project_data["description"],
        "only_english": project_data["only_english"]
    }
    with open(project_folder / "config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

    # regex.json (copy of regex patterns)
    with open(project_folder / "regex.json", "w", encoding="utf-8") as f:
        json.dump(project_data["regex_patterns"], f, indent=4, ensure_ascii=False)

    # reports.csv (with filename and pdf_path columns)
    csv_path = project_folder / "reports.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "pdf_path"])

    return str(project_folder)