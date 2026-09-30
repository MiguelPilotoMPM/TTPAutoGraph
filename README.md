# TTPAutoGraph

Open-source Python tool for the **automatic extraction and visual analysis of Tactics, Techniques and Procedures (TTPs) and Indicators of Compromise (IoCs)** from Cyber Threat Intelligence (CTI) reports in PDF format.

Developed as a Master's Thesis for the *Master's Degree in Cybersecurity* at the University of Alcalá (2026):

> **Estudio y desarrollo de una nueva herramienta para la detección de Técnicas, Tácticas y Procedimientos (TTPs) desde informes de inteligencia de amenazas.**
> (*Study and development of a new tool for detecting Tactics, Techniques and Procedures (TTPs) from threat intelligence reports.*)
> Author: Miguel Pinto Morales · Supervisor: Enrique de la Hoz de la Hoz · Co-supervisor: Laura María Cornejo Bueno

This work is part of the project *APT-GRAN: Intelligent Attribution of Advanced Persistent Threats in Cybersecurity using Neural Networks and Graph Modelling* (PIUAH25/IA-058), GHEODE research group.

## How it works

For each PDF report added to a project:

1. **Duplicates and language** — the report is skipped if it already exists in the project or is not in English (`langdetect`).
2. **Text and IoCs** — text extraction with PyMuPDF and IoC extraction with regular expressions configurable per project (`regex.json`).
3. **TTPs** — sentence-level classification with [TTPXHunter](https://github.com/nanda-rani/TTPXHunter-Actionable-Threat-Intelligence-Extraction-as-TTPs-from-Finished-Cyber-Threat-Reports) (SecureBERT fine-tuned on MITRE ATT&CK v15.1; Hugging Face model `nanda-rani/TTPXHunter`).

Results are stored as JSON and explored through five interactive graphs:

| Tab | Content |
|---|---|
| Reports | Reports linked by shared TTPs or IoCs |
| TTPs | Techniques that co-occur in the same report |
| TTP+Rep | Bipartite graph reports ↔ TTPs |
| IOC+Rep | Bipartite graph reports ↔ IoCs |
| Full | Reports, TTPs and IoCs in a single graph |

## Installation

Requires Python 3.10.

```bash
# Option A: conda
conda env create -f environment.yml        # Linux (CUDA)
conda env create -f environment_arm.yml    # macOS Apple Silicon
conda activate tfm

# Option B: venv + pip
python -m venv venv
source venv/bin/activate                   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

The TTPXHunter model is downloaded from Hugging Face the first time a report is processed (internet connection required).

## Usage

```bash
python main_home_page.py
```

- **NEW**: create a project (name, path, description and regular expressions).
- **OPEN**: open a project by selecting its `.project` file.
- **+ Add Report** (left panel): add and process a PDF.

Project structure:

```
<project>/
├── <project>.project      # absolute path of the project
├── config.json            # configuration and visual settings
├── regex.json             # IoC regular expressions
├── reports.csv            # added reports
├── reports_txt/           # text extracted from each PDF
└── reports_processed/     # JSON with IoCs (cti_info) and TTPs (ttp_info)
```

## Repository structure

```
├── main_home_page.py              # entry point (home screen)
├── base_page.py                   # main project window
├── create_new_project.py
├── add_new_report_to_project.py   # report processing pipeline
├── core_new_report/               # duplicates/language, text+IoCs, TTPXHunter
├── windows/                       # GUI panels and graphs
└── use_cases/                     # projects and results of the thesis use cases
```

## Use cases

Validation against the manually annotated [CTI-HAL](https://arxiv.org/abs/2504.05866) dataset (Penna et al., 2025).

| Folder | Use case |
|---|---|
| `use_cases/case1_case2_apt29/` | **1.** TTP extraction benchmark against CTI-HAL (APT29) · **2.** Visual traceability of shared TTPs in APT29 |
| `use_cases/case3_sandworm/`, `case3_wizardspider/`, `case3_oilrig/` | **3.** Attack pattern profiling per APT group |

Each `project/` folder is a TTPAutoGraph project that can be loaded with **OPEN**. The `.project`, `config.json` and `reports.csv` files keep the absolute paths of the original machine; to open them on another machine, update the path in `.project` and `config.json`.

**The original PDFs are not included**, as they are third-party reports; they can be obtained through CTI-HAL.

### Reproducing the use case 1 evaluation

```bash
pip install pandas seaborn matplotlib
cd use_cases/case1_case2_apt29/evaluation
python generate_heatmap.py      # target.csv (CTI-HAL) vs ttpxhunter.csv -> heatmap_ttpxhunter_apt29.png
```

`process.py` builds the list of unique TTPs per report from the JSON files in `reports_processed/` (run it inside that folder).

## Limitations

- TTPXHunter is trained on MITRE ATT&CK v15.1 (193 techniques).
- Only English reports with selectable text are processed.
- The model tends to over-detect TTPs; results are a starting point for the analyst, not a final classification.

## License

[MIT](LICENSE)
