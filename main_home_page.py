import math
import random
import tkinter as tk
import tkinter.filedialog as filedialog 
import customtkinter as ctk
import os

# ── Change the app name here ─────────────────────────────────────────────────
APP_NAME = "TTPAutoGraph"

# ── Theme and colors ──────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG_COLOR     = "#0d1117"
CARD_COLOR   = "#161b22"
BORDER_COLOR = "#30363d"
NODE_COLOR   = "#4a9eff"

# ── Animated graph ────────────────────────────────────────────────────────────
NODE_COUNT = 40
NODE_SPEED = 0.4
LINK_DIST  = 160

# ── Default regex set ─────────────────────────────────────────────────────────
DEFAULT_REGEX = {
    "technical_patterns": [
        {"name": "IPv4",             "regex": r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"},
        {"name": "IPv6",             "regex": r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b"},
        {"name": "MAC",              "regex": r"\b(?:[0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2}\b"},
        {"name": "URL HTTP",         "regex": r"\bhttp://[\w.-]+(?:\.[\w.-]+)+[/\w._-]*\b"},
        {"name": "URL HTTPS",        "regex": r"\bhttps://[\w.-]+(?:\.[\w.-]+)+[/\w._-]*\b"},
        {"name": "Mail",             "regex": r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"},
        {"name": "Hash",             "regex": r"\b[a-fA-F0-9]{32,64}\b"},
        {"name": "Malicious Domain", "regex": r"[a-zA-Z0-9.-]+\.(xyz|top|pw|bit)"},
        {"name": "Bitcoin Address",  "regex": r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b"},
        {"name": "Ethereum Address", "regex": r"\b0x[a-fA-F0-9]{40}\b"},
    ],
    "windows_patterns": [
        {"name": "File Path Windows", "regex": r"[a-zA-Z]:\\(?:[^\\/:?\"<>|\r\n]+\\)[^\\/:?\"<>|\r\n]"},
    ],
    "unix_patterns": [
        {"name": "File Path Unix", "regex": r"\b(?:/[^/\s]+)+/?\b"},
    ],
    "logical_patterns": [
        {"name": "DNI/NIE",     "regex": r"\b([XYZ]?\d{7,8}[A-Z])\b"},
        {"name": "IBAN",        "regex": r"\bES\d{2}[ ]?\d{4}[ ]?\d{4}[ ]?\d{2}[ ]?\d{10}\b"},
        {"name": "Credit Card", "regex": r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b"},
        {"name": "UUID",        "regex": r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"},
    ],
}


# ─────────────────────────────────────────────────────────────────────────────

class _Node:
    def __init__(self, w, h):
        self.x  = random.uniform(0, w)
        self.y  = random.uniform(0, h)
        self.vx = random.uniform(-NODE_SPEED, NODE_SPEED) or NODE_SPEED
        self.vy = random.uniform(-NODE_SPEED, NODE_SPEED) or NODE_SPEED
        self.r  = random.uniform(2, 4)

    def update(self, w, h):
        self.x += self.vx
        self.y += self.vy
        if not (0 < self.x < w): self.vx *= -1
        if not (0 < self.y < h): self.vy *= -1


def _blend(hex_fg, hex_bg, alpha):
    fr, fg_, fb = int(hex_fg[1:3], 16), int(hex_fg[3:5], 16), int(hex_fg[5:7], 16)
    br, bg_, bb = int(hex_bg[1:3], 16), int(hex_bg[3:5], 16), int(hex_bg[5:7], 16)
    return (f"#{int(fr*alpha+br*(1-alpha)):02x}"
            f"{int(fg_*alpha+bg_*(1-alpha)):02x}"
            f"{int(fb*alpha+bb*(1-alpha)):02x}")


# ─────────────────────────────────────────────────────────────────────────────

class HomePage(ctk.CTk):

    CARD_W       = 280
    CARD_H       = 190
    EXPAND_RATIO = 0.80

    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("960x620")
        self.resizable(False, False)
        self.minsize(960, 620)
        self.maxsize(960, 620)
        self.configure(fg_color=BG_COLOR)
        self.custom_regex_patterns = None  # Almacenará el dict del JSON cargado
        self.custom_regex_summary_label = None  # Label para mostrar info
        self._nodes: list[_Node] = []
        self._expanded = False

        self._canvas = tk.Canvas(self, bg=BG_COLOR, highlightthickness=0)
        self._canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        self._build_ui()
        self.after(100, self._init_nodes)
        self._animate()

    # ── Animated graph ────────────────────────────────────────────────────────

    def _init_nodes(self):
        w, h = self._canvas.winfo_width(), self._canvas.winfo_height()
        self._nodes = [_Node(w, h) for _ in range(NODE_COUNT)]

    def _animate(self):
        c = self._canvas
        w, h = c.winfo_width(), c.winfo_height()
        if not self._nodes and w > 1:
            self._init_nodes()
        c.delete("graph")
        for n in self._nodes:
            n.update(w, h)
        for i, a in enumerate(self._nodes):
            for b in self._nodes[i + 1:]:
                d = math.hypot(a.x - b.x, a.y - b.y)
                if d < LINK_DIST:
                    c.create_line(a.x, a.y, b.x, b.y,
                                  fill=_blend(NODE_COLOR, BG_COLOR, (1 - d / LINK_DIST) * 0.5),
                                  width=1, tags="graph")
        for n in self._nodes:
            c.create_oval(n.x - n.r, n.y - n.r, n.x + n.r, n.y + n.r,
                          fill=NODE_COLOR, outline="", tags="graph")
        self.after(30, self._animate)

    # ── Initial UI ────────────────────────────────────────────────────────────

    def _build_ui(self):
        ctk.CTkLabel(
            self, text=APP_NAME,
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color="#e6edf3", fg_color="transparent",
        ).place(relx=0.5, rely=0.15, anchor="center")

        self._card = ctk.CTkFrame(
            self,
            width=self.CARD_W, height=self.CARD_H,
            fg_color=CARD_COLOR, corner_radius=18,
            border_width=1, border_color=BORDER_COLOR,
        )
        self._card.place(relx=0.5, rely=0.52, anchor="center")
        self._card.pack_propagate(False)
        self._build_home_content()

    def _build_home_content(self):
        for w in self._card.winfo_children():
            w.destroy()

        ctk.CTkLabel(
            self._card, text="Projects",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#8b949e",
        ).pack(pady=(28, 18))

        row = ctk.CTkFrame(self._card, fg_color="transparent")
        row.pack()

        ctk.CTkButton(
            row, text="NEW", width=100, height=38, corner_radius=9,
            fg_color="#238636", hover_color="#2ea043",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_new,
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            row, text="OPEN", width=100, height=38, corner_radius=9,
            fg_color="#1f6feb", hover_color="#388bfd",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_open,
        ).pack(side="left", padx=10)

    def _expand_card(self):
        tw = int(self.winfo_width()  * self.EXPAND_RATIO)
        th = int(self.winfo_height() * self.EXPAND_RATIO)
        self._card.configure(width=tw, height=th)
        self.update_idletasks()

    def _on_new(self):
        if self._expanded:
            return
        self._expanded = True
        for w in self._card.winfo_children():
            w.destroy()
        self._expand_card()
        self._build_new_project_content()

    def _on_back(self):
        for w in self._card.winfo_children():
            w.destroy()
        self._expanded = False
        self._card.configure(width=self.CARD_W, height=self.CARD_H)
        self.update_idletasks()
        self._build_home_content()

    # ── Form content ──────────────────────────────────────────────────────────

    def _build_new_project_content(self):
        # ── Top bar with back arrow ───────────────────────────────────────────
        topbar = ctk.CTkFrame(self._card, fg_color="transparent", height=38)
        topbar.pack(fill="x", padx=8, pady=(6, 0))
        topbar.pack_propagate(False)

        ctk.CTkButton(
            topbar, text="<", width=34, height=28,
            corner_radius=8,
            fg_color="transparent", hover_color="#21262d",
            border_width=1, border_color=BORDER_COLOR,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#8b949e",
            command=self._on_back,
        ).pack(side="left")

        ctk.CTkLabel(
            topbar, text="New Project",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#8b949e", fg_color="transparent",
        ).pack(side="left", padx=10)

        # ── Tabs ───────────────────────────────────────────────────────────────
        tabs = ctk.CTkTabview(
            self._card,
            fg_color="#1c2128",
            segmented_button_fg_color=CARD_COLOR,
            segmented_button_selected_color="#1f6feb",
            segmented_button_selected_hover_color="#388bfd",
            segmented_button_unselected_color=CARD_COLOR,
            segmented_button_unselected_hover_color="#21262d",
            border_color=BORDER_COLOR, border_width=1,
        )
        tabs.pack(fill="both", expand=True, padx=10, pady=(4, 10))

        tabs.add("General")
        tabs.add("Regex")
   
        self._build_tab_general(tabs.tab("General"))
        self._build_tab_regex(tabs.tab("Regex"))

    def _clear_field_highlight(self, key):
        """Restore a field's default border and clear the global error message."""
        widget = self._entries.get(key)
        if widget:
            widget.configure(border_color=BORDER_COLOR)
        if self._error_label:
            self._error_label.configure(text="")

    def _clear_all_highlights(self):
        """Clear all red borders and the error message."""
        for key, widget in self._entries.items():
            if key != "description":  # description is not validated, kept for safety
                widget.configure(border_color=BORDER_COLOR)
        if self._error_label:
            self._error_label.configure(text="")

    # ── General tab ───────────────────────────────────────────────────────────

    def _build_tab_general(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, pady=(0, 6))

        self._entries = {}
        self._error_label = None  # error message label

        for label, key, multiline in [
            ("Project Name", "project_name", False),
            ("Project Path", "project_path", False),
            ("Description",  "description",  True),
        ]:
            ctk.CTkLabel(
                scroll, text=label,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#8b949e", anchor="w",
            ).pack(fill="x", padx=4, pady=(10, 2))

            if multiline:
                w = ctk.CTkTextbox(scroll, height=68, corner_radius=8,
                                border_width=1, border_color=BORDER_COLOR)
            else:
                w = ctk.CTkEntry(scroll, height=34, corner_radius=8,
                                border_width=1, border_color=BORDER_COLOR)
            w.pack(fill="x", padx=4)
            self._entries[key] = w

            # For required fields, remove red highlight while typing.
            if key in ("project_name", "project_path"):
                w.bind("<Key>", lambda e, k=key: self._clear_field_highlight(k))

        # Only English switch
        ctk.CTkLabel(
            scroll, text="Only English",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#8b949e", anchor="w",
        ).pack(fill="x", padx=4, pady=(10, 2))

        self._only_english = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(
            scroll, text="Filter non-English reports",
            variable=self._only_english, onvalue=True, offvalue=False,
            progress_color="#1f6feb",
        ).pack(anchor="w", padx=4, pady=(0, 10))

        # Label for validation errors
        self._error_label = ctk.CTkLabel(
            scroll, text="", font=ctk.CTkFont(size=11), text_color="#f85149"
        )
        self._error_label.pack(pady=(0, 5))

        # Create button
        ctk.CTkButton(
            parent, text="Create", height=36, corner_radius=9,
            fg_color="#238636", hover_color="#2ea043",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_create,
        ).pack(fill="x", padx=4, pady=(0, 4))

    # ── Regex tab ─────────────────────────────────────────────────────────────

    def _build_tab_regex(self, parent):
        ctk.CTkLabel(
            parent,
            text="i  By default the standard regex set is applied.\n"
                 "    Use 'Add Regex' to include custom patterns on top.",
            font=ctk.CTkFont(size=11),
            text_color="#8b949e", justify="left", anchor="w",
        ).pack(fill="x", padx=4, pady=(6, 4))

        scroll = ctk.CTkScrollableFrame(parent, fg_color="#0d1117", corner_radius=8)
        scroll.pack(fill="both", expand=True, padx=4, pady=(0, 6))

        for category, patterns in DEFAULT_REGEX.items():
            ctk.CTkLabel(
                scroll, text=f"  {category}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#4a9eff", anchor="w",
            ).pack(fill="x", pady=(8, 2))
            for p in patterns:
                ctk.CTkLabel(
                    scroll, text=f"    - {p['name']}",
                    font=ctk.CTkFont(size=11),
                    text_color="#c9d1d9", anchor="w",
                ).pack(fill="x", padx=6)

        btn_row = ctk.CTkFrame(parent, fg_color="transparent")
        btn_row.pack(fill="x", padx=4, pady=(0, 4))

        ctk.CTkButton(
            btn_row, text="+  Add Regex", height=36, corner_radius=9,
            fg_color="#21262d", hover_color="#30363d",
            border_width=1, border_color=BORDER_COLOR,
            font=ctk.CTkFont(size=12),
            command=self._on_add_regex,
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))

        ctk.CTkButton(
            btn_row, text="Create", height=36, corner_radius=9,
            fg_color="#238636", hover_color="#2ea043",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_create,
        ).pack(side="left", expand=True, fill="x")

        # --- Sección de patrones personalizados ---
        custom_frame = ctk.CTkFrame(parent, fg_color="transparent")
        custom_frame.pack(fill="x", padx=4, pady=(10, 4))

        ctk.CTkLabel(
            custom_frame, text="Custom Regex (loaded)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#4a9eff", anchor="w"
        ).pack(anchor="w")

        self.custom_regex_summary_label = ctk.CTkLabel(
            custom_frame, text="No custom regex loaded",
            font=ctk.CTkFont(size=11), text_color="#8b949e", anchor="w"
        )
        self.custom_regex_summary_label.pack(anchor="w", pady=(2, 5))

        btn_row = ctk.CTkFrame(custom_frame, fg_color="transparent")
        btn_row.pack(fill="x", pady=5)

        ctk.CTkButton(
            btn_row, text="+  Add Regex JSON", height=32, corner_radius=8,
            fg_color="#21262d", hover_color="#30363d",
            border_width=1, border_color=BORDER_COLOR,
            font=ctk.CTkFont(size=12),
            command=self._on_add_regex
        ).pack(side="left", padx=(0, 6))

        self._clear_custom_btn = ctk.CTkButton(
            btn_row, text="X  Clear", height=32, corner_radius=8,
            fg_color="#21262d", hover_color="#30363d",
            border_width=1, border_color=BORDER_COLOR,
            font=ctk.CTkFont(size=12), state="disabled",
            command=self._clear_custom_regex
        )
        self._clear_custom_btn.pack(side="left")

        # Botón Create (ya existe al final del método, lo dejamos igual)
        ctk.CTkButton(
            parent, text="Create", height=36, corner_radius=9,
            fg_color="#238636", hover_color="#2ea043",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_create,
        ).pack(fill="x", padx=4, pady=(0, 4))

    # ── Callbacks ────────────────────────────────────────────────────────────

    def _on_open(self):
        if self._expanded:
            return
        self._expanded = True
        for w in self._card.winfo_children():
            w.destroy()
        self._expand_card()
        self._build_open_project_content()

    def _build_open_project_content(self):
        self.update_idletasks()
        topbar = ctk.CTkFrame(self._card, fg_color="transparent", height=38)
        topbar.pack(fill="x", padx=8, pady=(6, 0))
        topbar.pack_propagate(False)
        ctk.CTkButton(
            topbar, text="<", width=34, height=28, corner_radius=8,
            fg_color="transparent", hover_color="#21262d",
            border_width=1, border_color=BORDER_COLOR,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#8b949e", command=self._on_back,
        ).pack(side="left")
        ctk.CTkLabel(
            topbar, text="Open Project", font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#8b949e", fg_color="transparent",
        ).pack(side="left", padx=10)

        main_frame = ctk.CTkFrame(self._card, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=30)
        ctk.CTkLabel(
            main_frame, text="Select a .project file",
            font=ctk.CTkFont(size=16, weight="bold"), text_color="#e6edf3"
        ).pack(pady=(0, 20))
        ctk.CTkButton(
            main_frame, text="Browse", width=200, height=40,
            fg_color="#1f6feb", hover_color="#388bfd",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._select_project_file
        ).pack(pady=10)
        self._selected_project_path_label = ctk.CTkLabel(
            main_frame, text="", font=ctk.CTkFont(size=11),
            text_color="#8b949e", wraplength=400
        )
        self._selected_project_path_label.pack(pady=10)
        self._load_btn = ctk.CTkButton(
            main_frame, text="Load Project", width=200, height=40,
            fg_color="#238636", hover_color="#2ea043",
            font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled", command=self._load_selected_project
        )
        self._load_btn.pack(pady=10)

    def _select_project_file(self):
        file_path = filedialog.askopenfilename(
            title="Select .project file",
            filetypes=[("Project files", "*.project"), ("All files", "*.*")]
        )
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                project_root = f.read().strip()
            if not os.path.exists(project_root):
                self._selected_project_path_label.configure(
                    text="Error: Project folder not found", text_color="#f85149"
                )
                self._load_btn.configure(state="disabled")
                return
            self._selected_project_path_label.configure(
                text=f"Project: {project_root}", text_color="#8b949e"
            )
            self._project_to_load = project_root
            self._load_btn.configure(state="normal")
        except Exception as e:
            self._selected_project_path_label.configure(
                text=f"Error reading file: {e}", text_color="#f85149"
            )
            self._load_btn.configure(state="disabled")

    def _load_selected_project(self):
        self.destroy()
        from base_page import BasePage
        new_window = BasePage(project_path=self._project_to_load)
        new_window.mainloop()

    def _on_create(self):
        # Clear previous highlights.
        self._clear_all_highlights()

        # Collect input values.
        project_name = self._entries["project_name"].get().strip()
        project_path = self._entries["project_path"].get().strip()
        # CTkTextbox uses a different get signature.
        description = self._entries["description"].get("1.0", tk.END).strip()
        only_english = self._only_english.get()

        # Validate required fields.
        errors = []
        if not project_name:
            errors.append("Project Name")
            self._entries["project_name"].configure(border_color="red")
        if not project_path:
            errors.append("Project Path")
            self._entries["project_path"].configure(border_color="red")

        if errors:
            mensaje = f"Missing required field(s): {', '.join(errors)}"
            if self._error_label:
                self._error_label.configure(text=mensaje)
            else:
                print(mensaje)
            return

        # Build regex dictionary: start with default patterns
        regex_to_use = {}
        for category, patterns in DEFAULT_REGEX.items():
            regex_to_use[category] = patterns.copy()  # copy to avoid modifying original

        # If custom regex patterns were loaded via "Add Regex", merge them
        if hasattr(self, 'custom_regex_patterns') and self.custom_regex_patterns:
            for category, patterns in self.custom_regex_patterns.items():
                if category in regex_to_use:
                    # Append custom patterns to existing category
                    regex_to_use[category].extend(patterns)
                else:
                    # New category, add it
                    regex_to_use[category] = patterns

        # Prepare project data
        project_data = {
            "name": project_name,
            "path": project_path,
            "description": description,
            "only_english": only_english,
            "regex_patterns": regex_to_use,
        }

        # Create the project
        try:
            from create_new_project import create_project
            created_path = create_project(project_data)
            print(f"Project created successfully at: {created_path}")
        except ImportError:
            error_msg = "Could not find create_new_project.py or the function create_project"
            if self._error_label:
                self._error_label.configure(text=error_msg)
            else:
                print(error_msg)
            return
        except Exception as e:
            error_msg = f"Error creating project: {e}"
            if self._error_label:
                self._error_label.configure(text=error_msg)
            else:
                print(error_msg)
            return

        # Close current window and open base_page
        self.destroy()
        from base_page import BasePage
        new_window = BasePage(project_path=created_path)
        new_window.mainloop()

    def _on_add_regex(self):
        from tkinter import filedialog, messagebox
        import json

        file_path = filedialog.askopenfilename(
            title="Select regex JSON file",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                custom = json.load(f)

            # Basic validation: must be a dict with each value being a list of dicts with 'name' and 'regex'
            if not isinstance(custom, dict):
                raise ValueError("The JSON file must be a dictionary with categories.")
            for category, patterns in custom.items():
                if not isinstance(patterns, list):
                    raise ValueError(f"The category '{category}' is not a list.")
                for p in patterns:
                    if not isinstance(p, dict) or "name" not in p or "regex" not in p:
                        raise ValueError(f"Invalid pattern in '{category}': missing 'name' or 'regex'.")

            self.custom_regex_patterns = custom
            # Update summary
            total = sum(len(patterns) for patterns in custom.values())
            categories = ", ".join(custom.keys())
            self.custom_regex_summary_label.configure(
                text=f"Loaded: {total} patterns from categories: {categories}",
                text_color="#c9d1d9"
            )
            self._clear_custom_btn.configure(state="normal")
            messagebox.showinfo("Regex Loaded", f"Loaded {total} custom patterns.\nThey will be combined with the default patterns when creating the project.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not load the file:\n{e}")

    def _clear_custom_regex(self):
        self.custom_regex_patterns = None
        self.custom_regex_summary_label.configure(
            text="No custom regex loaded", text_color="#8b949e"
        )
        self._clear_custom_btn.configure(state="disabled")

# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    HomePage().mainloop()
