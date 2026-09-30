"""
ttpxhunter_function.py

INPUTS:

    * txt Path: String

OUTPUTS:

    * Is processed: Boolean (True if the report is processed, False otherwise)
    * Extracted TTP information: Dictionary

DEFINITION:

    1- Extract the TTPS from the txt file and save in a TTP dictionary.
    2- Return True if the report is processed, False otherwise.
"""

import pickle
import nltk
from pathlib import Path

import torch
from transformers import RobertaTokenizer, RobertaForSequenceClassification

nltk.download("punkt_tab", quiet=True)

THRESHOLD       = 0.9
_LABEL_DICT_PATH = Path(__file__).parent / "label_dict.pkl"
_TTPID2NAME_PATH = Path(__file__).parent / "ttp_id_name.pkl"

# Model and label maps loaded once at module level (fixed model artifacts)
_device    = torch.device("cuda" if torch.cuda.is_available() else "cpu")
_model     = RobertaForSequenceClassification.from_pretrained("nanda-rani/TTPXHunter")
_tokenizer = RobertaTokenizer.from_pretrained("nanda-rani/TTPXHunter")
_model.to(_device)
_model.eval()

with open(_LABEL_DICT_PATH, "rb") as _f:
    _label_dict = {v: k for k, v in pickle.load(_f).items()}

with open(_TTPID2NAME_PATH, "rb") as _f:
    _ttpid_to_name = pickle.load(_f)


# ── helpers ───────────────────────────────────────────────────────────────────

def _clean_text(text: str) -> str:
    if not text:
        return ""
    cleaned = text[0]
    for char in text[1:]:
        if not (char == "\n" and cleaned[-1] == "\n"):
            cleaned += char
    return cleaned.replace("\t", " ").replace("\\'", "'")


def _sentences(text: str) -> list[str]:
    result = []
    for sent in nltk.sent_tokenize(text):
        result.extend(line for line in sent.split("\n") if line)
    return result


def _extract_ttps(sentences: list[str]) -> list[dict]:
    results = []
    for text in sentences:
        inputs = _tokenizer(
            text, padding=True, truncation=True,
            max_length=256, return_tensors="pt"
        ).to(_device)

        with torch.no_grad():
            logits = _model(**inputs).logits

        probs            = torch.softmax(logits, dim=1)
        max_prob, pred   = torch.max(probs, dim=1)

        if max_prob.item() > THRESHOLD:
            label_str    = _model.config.id2label[pred.item()]
            mapped_label = int(label_str.split("_")[1])
            if mapped_label in _label_dict:
                results.append({"context": text, "technique": _label_dict[mapped_label]})
    return results


# ── main function ─────────────────────────────────────────────────────────────

def ttpxhunter(txt_path: str) -> tuple[bool, dict]:
    txt = Path(txt_path)

    try:
        text        = _clean_text(txt.read_text(encoding="utf-8", errors="ignore"))
        ttp_results = _extract_ttps(_sentences(text))

        ttps = [
            {
                "context":        item["context"],
                "technique":      item["technique"],
                "technique_name": _ttpid_to_name.get(item["technique"], ""),
            }
            for item in ttp_results
        ]

        ttp_info = {
            "file_name":  txt.name,
            "total_ttps": len(ttps),
            "ttps":       ttps,
        }

    except Exception:
        return False, {}

    return True, ttp_info
