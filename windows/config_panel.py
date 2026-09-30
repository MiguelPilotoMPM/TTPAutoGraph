import csv
import os
import sys
import threading
import tkinter.filedialog as filedialog
from tkinter import messagebox
from pathlib import Path

import customtkinter as ctk

CARD_COLOR   = "#161b22"
BORDER_COLOR = "#30363d"

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ── Progress dialog ───────────────────────────────────────────────────────────

class _ProgressDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Processing report...")
        self.geometry("360x130")
        self.resizable(False, False)
        self.grab_set()

        ctk.CTkLabel(
            self, text="Adding report — this may take a moment...",
            font=ctk.CTkFont(size=12), text_color="#c9d1d9",
        ).pack(pady=(24, 10))

        self._bar = ctk.CTkProgressBar(self, mode="indeterminate", width=300)
        self._bar.pack(pady=(0, 20))
        self._bar.start()

    def close(self):
        self._bar.stop()
        self.destroy()


# ── Config panel ──────────────────────────────────────────────────────────────

class ConfigPanel(ctk.CTkFrame):

    def __init__(self, parent, project_path, on_refresh=None):
        super().__init__(parent, fg_color="transparent")
        self.project_path = Path(project_path) if project_path else None
        self.on_refresh   = on_refresh
        self._all_reports = []
        self._build()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        # ── Search bar ────────────────────────────────────────────────────────
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._apply_filter())

        ctk.CTkEntry(
            self, textvariable=self._search_var,
            placeholder_text="Search reports...",
            height=32, corner_radius=8,
            border_width=1, border_color=BORDER_COLOR,
            font=ctk.CTkFont(size=12),
        ).pack(fill="x", padx=6, pady=(6, 4))

        self._count_label = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=11), text_color="#8b949e"
        )
        self._count_label.pack(anchor="w", padx=8, pady=(0, 2))

        self._list_frame = ctk.CTkScrollableFrame(
            self, fg_color="#0d1117", corner_radius=8
        )
        self._list_frame.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        ctk.CTkButton(
            self, text="+ Add Report", height=36, corner_radius=9,
            fg_color="#238636", hover_color="#2ea043",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_add,
        ).pack(fill="x", padx=6, pady=(0, 6))

        self.refresh()

    # ── Data ──────────────────────────────────────────────────────────────────

    def refresh(self):
        self._all_reports = self._load_reports()
        self._apply_filter()

    def _apply_filter(self):
        query = self._search_var.get().strip().lower()
        filtered = [
            (f, p) for f, p in self._all_reports
            if query in f.lower()
        ]
        for w in self._list_frame.winfo_children():
            w.destroy()
        total = len(self._all_reports)
        shown = len(filtered)
        self._count_label.configure(
            text=f"{shown} of {total} report(s)" if query else f"{total} report(s)"
        )
        for filename, pdf_path in filtered:
            self._add_row(filename, pdf_path)

    def _load_reports(self):
        if not self.project_path:
            return []
        csv_path = self.project_path / "reports.csv"
        if not csv_path.exists():
            return []
        try:
            with open(csv_path, newline="", encoding="utf-8") as f:
                return [(r["filename"], r.get("pdf_path", "")) for r in csv.DictReader(f)]
        except Exception:
            return []

    # ── Row widget ────────────────────────────────────────────────────────────

    def _add_row(self, filename, pdf_path):
        row = ctk.CTkFrame(self._list_frame, fg_color=CARD_COLOR, corner_radius=8)
        row.pack(fill="x", pady=3, padx=2)

        # Pack the button FIRST so it always gets its reserved space
        ctk.CTkButton(
            row, text="X", width=28, height=28, corner_radius=6,
            fg_color="#21262d", hover_color="#f85149",
            border_width=1, border_color=BORDER_COLOR,
            font=ctk.CTkFont(size=11, weight="bold"), text_color="#8b949e",
            command=lambda f=filename: self._on_delete(f),
        ).pack(side="right", padx=6, pady=6)

        # Label takes the remaining space
        ctk.CTkLabel(
            row, text=filename, font=ctk.CTkFont(size=11),
            text_color="#c9d1d9", anchor="w", wraplength=190,
        ).pack(side="left", fill="x", expand=True, padx=10, pady=8)

    # ── Add report (with progress bar) ────────────────────────────────────────

    def _on_add(self):
        if not self.project_path:
            return
        pdf_path = filedialog.askopenfilename(
            title="Select PDF report",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        if not pdf_path:
            return

        dialog = _ProgressDialog(self.winfo_toplevel())
        result = {"success": None, "error": None}

        def run():
            try:
                if _BASE_DIR not in sys.path:
                    sys.path.insert(0, _BASE_DIR)
                from add_new_report_to_project import add_new_report
                result["success"] = add_new_report(str(self.project_path), pdf_path)
            except Exception as e:
                result["error"] = str(e)
            finally:
                # Schedule UI update back on the main thread
                self.after(0, lambda: self._on_add_done(dialog, result))

        threading.Thread(target=run, daemon=True).start()

    def _on_add_done(self, dialog, result):
        dialog.close()
        if result["error"]:
            messagebox.showerror("Error", result["error"])
        elif result["success"]:
            messagebox.showinfo("Success", "Report added successfully.")
            self.refresh()
            if self.on_refresh:
                self.on_refresh()
        else:
            messagebox.showerror(
                "Error", "Failed to add report (duplicate or unsupported language)."
            )

    # ── Delete report ─────────────────────────────────────────────────────────

    def _on_delete(self, filename):
        if not messagebox.askyesno("Delete", f"Delete '{filename}'?"):
            return
        self._remove_csv_row(filename)
        for folder, ext in [("reports_processed", ".json"), ("reports_txt", ".txt")]:
            p = self.project_path / folder / f"{filename}{ext}"
            if p.exists():
                p.unlink()
        self.refresh()
        if self.on_refresh:
            self.on_refresh()

    def _remove_csv_row(self, filename):
        csv_path = self.project_path / "reports.csv"
        try:
            with open(csv_path, newline="", encoding="utf-8") as f:
                rows = [r for r in csv.DictReader(f) if r["filename"] != filename]
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["filename", "pdf_path"])
                w.writeheader()
                w.writerows(rows)
        except Exception:
            pass
