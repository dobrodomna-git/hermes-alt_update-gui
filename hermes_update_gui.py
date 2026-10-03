#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hermes_update_gui.py - graphical wrapper for `hermes update` (stdlib-only).

Interface languages: English and Russian, switchable at runtime.
"""

import ctypes
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk

VERSION = "1.1.0"

BG = "#101418"
PANEL = "#171c22"
FG = "#e6e6e6"
ACCENT = "#7aa2f7"
SUCCESS = "#3fb950"
ERROR = "#f85149"
WARNING = "#d29922"
BORDER = "#30363d"
GRAY = "#8b949e"
HILITE = "#1b2430"

SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

# ---------------------------------------------------------------- i18n ------
# Every user-visible string lives here. Add a language by adding a dict.
I18N = {
    "en": {
        "title": "Hermes ALT - update  v%s",
        "lang_button": "RU",
        "waiting": "waiting",
        "time": "time: %02d:%02d",
        "counters": "connections: %d   downloads: %d   errors: %d",
        "pending_word": "pending",
        "idle": "stage running %d min with no output - normal for the desktop build",
        "start": "Start update",
        "check": "Check only",
        "cancel": "Cancel",
        "open_log": "Open log",
        "open_dir": "Open Hermes folder",
        "b_complete": "UPDATE COMPLETE",
        "b_aborted": "UPDATE ABORTED / ERROR",
        "b_cancelled": "UPDATE CANCELLED",
        "b_notfound": "HERMES NOT FOUND",
        "b_available": "Update available",
        "b_check_done": "Check finished",
        "d_close": "Close this window and start Hermes again (desktop shortcut).",
        "d_close_err": "Close the installer; details are in the log (\"Open log\").",
        "d_exit": "exit code: %s",
        "d_log": "log: %s",
        "d_nf_1": "Hermes Agent installation was not found on this computer",
        "d_nf_2": "checked path: %s",
        "d_nf_3": "point it manually: hermes_update_gui.py --repo <path to hermes-agent>",
        "d_no_exe": "hermes.exe not found at %s",
        "d_launch_fail": "could not start the updater: %s",
        "d_cancelled": "cancelled by user",
        "g_start": "wrapper started; log: %s",
        "g_stage": "stage: %s",
        "g_launch": "launching: %s",
        "g_final_cancel": "final: cancelled by user",
        "g_final_cancel_close": "final: cancelled by user (window closed)",
        "g_final_check": "final: check finished exit=%s",
        "g_final_ok": "final: update complete exit=0",
        "g_final_err": "final: error exit=%s",
        "g_cancel": "cancel: stopping the child process",
        "g_close": "window closed",
        "g_lost": "[ERROR] lost contact with the updater process: %s",
        "g_traceback": "traceback: ",
        "g_nf": "Hermes not found; checked: %s",
        "g_no_exe": "hermes.exe not found at %s",
        "lock_title": "Hermes ALT - update",
        "lock_1": "Another copy of the installer is already running.",
        "lock_2": "Close it, or wait for it to finish.",
    },
    "ru": {
        "title": "Hermes ALT - обновление  v%s",
        "lang_button": "EN",
        "waiting": "ожидание",
        "time": "время: %02d:%02d",
        "counters": "соединений: %d   загрузок: %d   ошибок: %d",
        "pending_word": "ожидается",
        "idle": "этап идёт %d мин без вывода - это нормально для сборки десктопа",
        "start": "Начать обновление",
        "check": "Только проверка",
        "cancel": "Отменить",
        "open_log": "Открыть лог",
        "open_dir": "Открыть папку Hermes",
        "b_complete": "ОБНОВЛЕНИЕ ЗАВЕРШЕНО",
        "b_aborted": "ОБНОВЛЕНИЕ ПРЕРВАНО / ОШИБКА",
        "b_cancelled": "ОБНОВЛЕНИЕ ОТМЕНЕНО",
        "b_notfound": "HERMES НЕ НАЙДЕН",
        "b_available": "Обновление доступно",
        "b_check_done": "Проверка завершена",
        "d_close": "Закройте это окно и запустите Hermes заново (ярлык на рабочем столе).",
        "d_close_err": "Закройте установщик; подробности в логе (кнопка «Открыть лог»).",
        "d_exit": "код выхода: %s",
        "d_log": "лог: %s",
        "d_nf_1": "установка Hermes Agent не найдена на этом компьютере",
        "d_nf_2": "проверенный путь: %s",
        "d_nf_3": "укажите путь вручную: hermes_update_gui.py --repo <путь к hermes-agent>",
        "d_no_exe": "hermes.exe не найден по пути %s",
        "d_launch_fail": "не удалось запустить апдейтер: %s",
        "d_cancelled": "отменено пользователем",
        "g_start": "старт обёртки; лог: %s",
        "g_stage": "этап: %s",
        "g_launch": "запуск: %s",
        "g_final_cancel": "финал: отменено пользователем",
        "g_final_cancel_close": "финал: отменено пользователем (окно закрыто)",
        "g_final_check": "финал: проверка завершена exit=%s",
        "g_final_ok": "финал: обновление завершено exit=0",
        "g_final_err": "финал: ошибка exit=%s",
        "g_cancel": "отмена: остановка дочернего процесса",
        "g_close": "закрытие окна",
        "g_lost": "[ERROR] потеря связи с процессом: %s",
        "g_traceback": "traceback: ",
        "g_nf": "Hermes не найден; проверялись: %s",
        "g_no_exe": "hermes.exe не найден по пути %s",
        "lock_title": "Hermes ALT - обновление",
        "lock_1": "Уже запущена другая копия установщика.",
        "lock_2": "Закройте её или дождитесь завершения.",
    },
}

STAGES = [
    {"id": "prep", "weight": 5,
     "name": {"en": "Preparing Hermes", "ru": "Подготовка Hermes"},
     "markers": [("stopping windows gateway",), ("stopping",), ("preparing update",)]},
    {"id": "fetch", "weight": 10,
     "name": {"en": "Connecting to repository", "ru": "Соединение с репозиторием"},
     "markers": [("fetching updates",)]},
    {"id": "pull", "weight": 15,
     "name": {"en": "Downloading changes", "ru": "Загрузка изменений"},
     "markers": [("pulling updates",), ("found ", "new commit"),
                 ("restoring local changes",), ("stashing",)]},
    {"id": "deps", "weight": 15,
     "name": {"en": "Dependencies and binaries", "ru": "Зависимости и бинарники"},
     "markers": [("installing node.js dependencies",), ("node.js dependencies",),
                 ("preparing node dependencies",), ("node dependencies",),
                 ("installing python dependencies",), ("python dependencies",),
                 ("refreshing",),
                 ("warming npx cache",), ("installing agent-browser",),
                 ("installing cua-driver",), ("install failed",), ("download failed",)]},
    {"id": "webui", "weight": 10,
     "name": {"en": "Building web UI", "ru": "Сборка веб-интерфейса"},
     "markers": [("building web ui",), ("building the web ui",), ("web ui",),
                 ("building the tui",)]},
    {"id": "desktop", "weight": 30,
     "name": {"en": "Rebuilding the app", "ru": "Пересборка приложения"},
     "markers": [("checking if desktop app needs rebuilding",),
                 ("installing desktop workspace dependencies",),
                 ("building desktop packaged app",), ("packaging the desktop app",),
                 ("stage-native-deps",), ("set-exe-identity",), ("assert-dist-built",)]},
    {"id": "config", "weight": 10,
     "name": {"en": "Skills and configuration", "ru": "Навыки и конфигурация"},
     "markers": [("syncing bundled skills",), ("checking configuration for new options",),
                 ("config format updated",)]},
    {"id": "done", "weight": 5,
     "name": {"en": "Finishing", "ru": "Завершение"},
     "markers": [("update complete",), ("gateway started",)]},
]

MAX_LOG_LINES = 2000
LANG_FILE = "hermes-alt-update-gui.lang"


def classify(low):
    """Map a lowercased updater line to a stage index (first match wins)."""
    for idx, st in enumerate(STAGES):
        for marker in st["markers"]:
            if all(m in low for m in marker):
                return idx
    return None


def detect_language():
    """Pick the interface language: Windows UI language, else English."""
    try:
        lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3F
        if lang_id in (0x19, 0x18, 0x04, 0x0B, 0x0C, 0x15, 0x22, 0x23, 0x09, 0x1C,
                       0x11, 0x13, 0x0F, 0x1A, 0x12, 0x1F, 0x08, 0x21, 0x1E):
            return "ru"
    except Exception:
        pass
    return "en"


def saved_language():
    for base in (os.environ.get("LOCALAPPDATA"), os.environ.get("APPDATA")):
        if not base:
            continue
        path = os.path.join(base, "hermes", LANG_FILE)
        try:
            with open(path, encoding="utf-8") as handle:
                value = handle.read().strip().lower()
            if value in I18N:
                return value
        except OSError:
            continue
    return None


def save_language(lang):
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    if not base:
        return
    path = os.path.join(base, "hermes", LANG_FILE)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(lang)
    except OSError:
        pass


def find_hermes():
    """Locate a Hermes Agent checkout on this machine. Returns an absolute
    repo path or None. Deliberately limited to known locations - no disk scan."""
    cands = []
    env_home = os.environ.get("HERMES_HOME")
    if env_home:
        cands.append(os.path.join(env_home, "hermes-agent"))
    la = os.environ.get("LOCALAPPDATA")
    if la:
        cands.append(os.path.join(la, "hermes", "hermes-agent"))
    home = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    cands.append(os.path.join(home, ".hermes", "hermes-agent"))
    cands.append(os.path.join(home, "hermes-agent"))
    exe = shutil.which("hermes")
    if exe:
        d = os.path.dirname(os.path.abspath(exe))  # ...\venv\Scripts
        for _ in range(3):
            parent = os.path.dirname(d)
            if parent == d:
                break
            if os.path.isdir(os.path.join(parent, "venv")):
                cands.append(parent)
                break
            d = parent
    for c in cands:
        if not c or not os.path.isdir(c):
            continue
        if (os.path.exists(os.path.join(c, "venv", "Scripts", "hermes.exe"))
                or os.path.exists(os.path.join(c, "venv", "bin", "hermes"))
                or os.path.exists(os.path.join(c, "pyproject.toml"))):
            return os.path.abspath(c)
    return None


def acquire_single_instance():
    """Windows named mutex: returns a handle for the first instance, None if
    another copy is already running. The OS releases it even on a hard kill."""
    if os.name != "nt":
        return "ok"
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.CreateMutexW(None, False, "Local\\HermesAltUpdateGUI")
        if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            if handle:
                kernel32.CloseHandle(handle)
            return None
        return handle
    except Exception:
        return "ok"  # never block the updater over a lock quirk


class HermesUpdateGUI:
    def __init__(self, argv):
        self.check_only = "--check" in argv
        self.mock_path = None
        if "--mock" in argv:
            i = argv.index("--mock")
            if i + 1 < len(argv):
                self.mock_path = os.path.abspath(argv[i + 1])
        if "--repo" in argv:
            i = argv.index("--repo")
            if i + 1 < len(argv):
                self.repo = os.path.abspath(
                    os.path.expandvars(os.path.expanduser(argv[i + 1])))
        else:
            self.repo = find_hermes() or os.path.expandvars(
                r"%LOCALAPPDATA%\hermes\hermes-agent")
        self.repo_found = os.path.isdir(self.repo)

        lang = None
        if "--lang" in argv:
            i = argv.index("--lang")
            if i + 1 < len(argv) and argv[i + 1].lower() in I18N:
                lang = argv[i + 1].lower()
        if lang is None:
            env_lang = (os.environ.get("HERMES_UPDATE_GUI_LANG") or "").strip().lower()
            if env_lang in I18N:
                lang = env_lang
        if lang is None:
            lang = saved_language() or detect_language()
        self.lang = lang

        self.hermes_dir = (os.path.dirname(self.repo) if self.repo_found
                           else os.path.join(os.path.expandvars(r"%LOCALAPPDATA%"),
                                             "hermes"))
        log_dir = os.path.join(self.hermes_dir, "logs")
        try:
            os.makedirs(log_dir, exist_ok=True)
        except OSError:
            log_dir = os.path.expandvars(r"%TEMP%")
        self.log_path = os.path.join(
            log_dir, "update-gui-%s.log" % time.strftime("%Y-%m-%d-%H%M%S"))
        self.log_f = open(self.log_path, "w", encoding="utf-8")

        self.q = queue.Queue()
        self.proc = None
        self.running = False
        self.cancelled = False
        self.force_done = False
        self.current_idx = -1
        self.stage_status = ["pending"] * len(STAGES)
        self.progress = 0.0
        self.connections = 0
        self.downloads = 0
        self.errors = 0
        self.error_lines = []
        self.saw_complete = False
        self.version_line = None
        self.available_line = None
        self.uptodate_line = None
        self.start_time = None
        self.last_line_time = None
        self.spin_idx = 0
        self.banner_state = None  # (color, title_key, detail_args) for re-render

        self._build_ui()
        self.log_gui(self.T("g_start") % self.log_path)
        self.root.after(50, self._poll)
        self.root.after(1000, self._tick)
        if self.check_only or self.mock_path:
            self.root.after(200, self.start)

    # ------------------------------------------------------------- i18n ------
    def T(self, key):
        return I18N[self.lang][key]

    def stage_name(self, idx):
        return STAGES[idx]["name"][self.lang]

    def toggle_language(self):
        self.lang = "ru" if self.lang == "en" else "en"
        save_language(self.lang)
        self.log_gui("[gui] language: %s" % self.lang)
        self._relabel()

    def _relabel(self):
        self.root.title(self.T("title") % VERSION)
        self.lang_btn.config(text=self.T("lang_button"))
        self.start_btn.config(text=self.T("start"))
        self.check_btn.config(text=self.T("check"))
        self.cancel_btn.config(text=self.T("cancel"))
        self.open_log_btn.config(text=self.T("open_log"))
        self.open_dir_btn.config(text=self.T("open_dir"))
        self.timer_label.config(text=self.T("time") % divmod(
            int(time.time() - self.start_time) if self.start_time else 0, 60))
        self._update_counters()
        self._update_header()
        self._refresh_stages()
        if self.banner_state is not None:
            color, title_key, specs = self.banner_state
            self._show_banner(color, title_key, specs)

    # ---------------------------------------------------------------- ui -----
    def _build_ui(self):
        self.root = tk.Tk()
        self.root.title(self.T("title") % VERSION)
        self.root.geometry("880x620")
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Dark.Horizontal.TProgressbar", troughcolor=BORDER,
                        background=ACCENT, bordercolor=BORDER,
                        lightcolor=ACCENT, darkcolor=ACCENT, thickness=14)

        header = tk.Frame(self.root, bg=PANEL, highlightbackground=BORDER,
                          highlightthickness=1)
        header.grid(row=0, column=0, sticky="we")
        self.lang_btn = tk.Button(header, text=self.T("lang_button"),
                                  command=self.toggle_language, bg=PANEL, fg=ACCENT,
                                  activebackground=ACCENT, activeforeground=BG,
                                  font=("Segoe UI", 9, "bold"), relief="flat",
                                  width=4, padx=6, pady=2)
        self.lang_btn.pack(side="right", padx=(6, 12))
        self.stage_header = tk.Label(header, text=self.T("waiting"), bg=PANEL, fg=ACCENT,
                                     font=("Segoe UI", 14, "bold"), anchor="w")
        self.stage_header.pack(side="left", padx=12, pady=8)
        self.timer_label = tk.Label(header, text=self.T("time") % (0, 0), bg=PANEL, fg=GRAY,
                                    font=("Segoe UI", 10))
        self.timer_label.pack(side="right", padx=12)

        prow = tk.Frame(self.root, bg=BG)
        prow.grid(row=1, column=0, sticky="we", padx=10, pady=(8, 2))
        self.progressbar = ttk.Progressbar(prow, style="Dark.Horizontal.TProgressbar",
                                           orient="horizontal", mode="determinate",
                                           maximum=100)
        self.progressbar.pack(side="left", fill="x", expand=True)
        self.percent_label = tk.Label(prow, text="0%", bg=BG, fg=FG,
                                      font=("Segoe UI", 10, "bold"), width=5)
        self.percent_label.pack(side="right", padx=6)

        crow = tk.Frame(self.root, bg=BG)
        crow.grid(row=2, column=0, sticky="we", padx=10)
        self.counters_label = tk.Label(crow, text=self.T("counters") % (0, 0, 0),
                                       bg=BG, fg=GRAY, font=("Segoe UI", 9), anchor="w")
        self.counters_label.pack(side="left")
        self.idle_label = tk.Label(crow, text="", bg=BG, fg=WARNING,
                                   font=("Segoe UI", 9), anchor="e")

        main = tk.Frame(self.root, bg=BG)
        main.grid(row=3, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(3, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        left = tk.Frame(main, bg=PANEL, width=300, highlightbackground=BORDER,
                        highlightthickness=1)
        left.grid(row=0, column=0, sticky="ns", padx=(10, 5), pady=5)
        left.grid_propagate(False)
        left.columnconfigure(0, weight=1)
        self.stage_rows = []
        for i, st in enumerate(STAGES):
            row = tk.Frame(left, bg=PANEL)
            row.grid(row=i, column=0, sticky="we", padx=8, pady=4)
            row.columnconfigure(1, weight=1)
            icon = tk.Label(row, text=self.T("pending_word"), width=10, anchor="w",
                            bg=PANEL, fg=GRAY, font=("Segoe UI", 9))
            icon.grid(row=0, column=0, sticky="w")
            name = tk.Label(row, text="%d. %s" % (i + 1, self.stage_name(i)),
                            anchor="w", bg=PANEL, fg=FG, font=("Segoe UI", 10))
            name.grid(row=0, column=1, sticky="we")
            self.stage_rows.append((row, icon, name))

        right = tk.Frame(main, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        right.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=5)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)
        self.log_widget = tk.Text(right, bg="#0c1014", fg=FG, insertbackground=FG,
                                  font=("Consolas", 9), wrap="char", state="disabled",
                                  relief="flat", borderwidth=0)
        self.log_widget.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(right, orient="vertical", command=self.log_widget.yview)
        sb.grid(row=0, column=1, sticky="ns")
        style = self.root.style if hasattr(self.root, "style") else ttk.Style()
        style.configure("Dark.Vertical.TScrollbar", background="#3a4350",
                        troughcolor="#12161b", bordercolor=BORDER,
                        lightcolor="#4a5566", darkcolor="#2a323d",
                        arrowsize=12, relief="flat")
        sb.configure(style="Dark.Vertical.TScrollbar")
        self.log_widget.configure(yscrollcommand=sb.set)
        self.log_widget.tag_configure("err", foreground=ERROR)
        self.log_widget.tag_configure("gui", foreground=ACCENT)

        self.start_frame = tk.Frame(self.root, bg=BG)
        self.start_frame.grid(row=4, column=0, sticky="we", pady=10)
        big_font = ("Segoe UI", 12, "bold")
        self.start_btn = tk.Button(self.start_frame, text=self.T("start"),
                                   command=self.start, bg=PANEL, fg=FG,
                                   activebackground=ACCENT, activeforeground=BG,
                                   font=big_font, relief="flat", padx=24, pady=10)
        self.start_btn.pack(side="left", padx=(10, 6))
        self.check_btn = tk.Button(self.start_frame, text=self.T("check"),
                                   command=self.start_check, bg=PANEL, fg=FG,
                                   activebackground=ACCENT, activeforeground=BG,
                                   font=("Segoe UI", 11), relief="flat", padx=16, pady=10)
        self.check_btn.pack(side="left", padx=6)

        self.banner_frame = tk.Frame(self.root, bg=PANEL, highlightbackground=BORDER,
                                     highlightthickness=1)
        self.banner_title = tk.Label(self.banner_frame, text="", bg=PANEL, fg=FG,
                                     font=("Segoe UI", 13, "bold"), anchor="w")
        self.banner_title.pack(fill="x", padx=12, pady=(8, 2))
        self.banner_detail = tk.Label(self.banner_frame, text="", bg=PANEL, fg=FG,
                                      font=("Segoe UI", 9), anchor="w", justify="left",
                                      wraplength=820)
        self.banner_detail.pack(fill="x", padx=12, pady=(0, 8))

        btns = tk.Frame(self.root, bg=BG)
        btns.grid(row=5, column=0, sticky="we", padx=10, pady=(4, 10))
        self.cancel_btn = tk.Button(btns, text=self.T("cancel"), command=self.cancel,
                                    bg=PANEL, fg=WARNING, activebackground=WARNING,
                                    activeforeground=BG, font=("Segoe UI", 10),
                                    relief="flat", padx=16, pady=6)
        self.open_log_btn = tk.Button(btns, text=self.T("open_log"), command=self.open_log,
                                      bg=PANEL, fg=FG, activebackground=ACCENT,
                                      activeforeground=BG, font=("Segoe UI", 10),
                                      relief="flat", padx=16, pady=6)
        self.open_dir_btn = tk.Button(btns, text=self.T("open_dir"),
                                      command=self.open_hermes_dir, bg=PANEL, fg=FG,
                                      activebackground=ACCENT, activeforeground=BG,
                                      font=("Segoe UI", 10), relief="flat", padx=16, pady=6)
        self.cancel_btn.pack(side="left")

    def start_check(self):
        self.check_only = True
        self.start()

    def build_cmd(self):
        if self.mock_path:
            py = os.path.join(self.repo, "venv", "Scripts", "python.exe")
            if not os.path.exists(py):
                py = sys.executable
            return [py, self.mock_path]
        hermes = os.path.join(self.repo, "venv", "Scripts", "hermes.exe")
        if not os.path.exists(hermes):
            return None
        if self.check_only:
            return [hermes, "update", "--check", "--branch", "main"]
        return [hermes, "update", "--branch", "main", "--yes", "--keep-stash"]

    def start(self):
        if self.running:
            return
        cmd = self.build_cmd()
        if cmd is None:
            path = os.path.join(self.repo, "venv", "Scripts", "hermes.exe")
            if not self.repo_found:
                self.log_gui(self.T("g_nf") % self.repo)
                self._show_banner(ERROR, "b_notfound",
                                  ["d_nf_1", ("d_nf_2", (self.repo,)), "d_nf_3",
                                   ("d_log", (self.log_path,))])
            else:
                self.log_gui(self.T("g_no_exe") % path)
                self._show_banner(ERROR, "b_aborted",
                                  [("d_no_exe", (path,)), ("d_log", (self.log_path,))])
            self.start_frame.grid_remove()
            self.open_log_btn.pack(side="right", padx=6)
            self.open_dir_btn.pack(side="right", padx=6)
            return
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["HERMES_UPDATE_STEP_IDLE_SECONDS"] = "1800"
        cwd = self.repo if os.path.isdir(self.repo) else None
        try:
            popen_kwargs = dict(
                cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL, text=True, encoding="utf-8",
                errors="replace", env=env)
            if os.name == "nt":
                # pythonw has no console; without this a black console window
                # flashes for the whole update.
                popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            self.proc = subprocess.Popen(cmd, **popen_kwargs)
        except OSError as exc:
            self.log_gui(self.T("d_launch_fail") % exc)
            self._show_banner(ERROR, "b_aborted",
                              [("d_launch_fail", (exc,)), ("d_log", (self.log_path,))])
            self.start_frame.grid_remove()
            self.open_log_btn.pack(side="right", padx=6)
            return
        self.running = True
        self.start_time = time.time()
        self.last_line_time = time.time()
        self.start_frame.grid_remove()
        self.log_gui(self.T("g_launch") % " ".join(cmd))
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self):
        code = -1
        try:
            for raw in self.proc.stdout:
                line = raw.rstrip()
                if line:
                    self.q.put(("line", line))
            code = self.proc.wait()
        except Exception as exc:
            self.q.put(("line", self.T("g_lost") % exc))
        self.q.put(("exit", code))

    def _poll(self):
        try:
            while True:
                kind, data = self.q.get_nowait()
                if kind == "line":
                    self._handle_line(data)
                elif kind == "exit":
                    self._on_exit(data)
        except queue.Empty:
            pass
        except tk.TclError:
            return
        try:
            self.root.after(50, self._poll)
        except tk.TclError:
            pass

    def _tick(self):
        try:
            if self.running:
                elapsed = int(time.time() - self.start_time)
                self.timer_label.config(text=self.T("time") % divmod(elapsed, 60))
                idle = time.time() - self.last_line_time
                if idle > 120:
                    self.idle_label.config(text=self.T("idle") % int(idle // 60))
                    self.idle_label.pack(side="right", padx=6)
                else:
                    self.idle_label.pack_forget()
                self.spin_idx += 1
                self._refresh_stages()
        except tk.TclError:
            return
        try:
            self.root.after(1000, self._tick)
        except tk.TclError:
            pass

    def _classify(self, low):
        return classify(low)

    def _handle_line(self, line):
        self.write_log(line)
        self.last_line_time = time.time()
        low = line.lower()
        is_err = ("✗" in line) or ("[error]" in low) or ("failed" in low) or ("error" in low)
        if is_err:
            self.errors += 1
            self.error_lines.append(line)
        if "https://" in line and any(k in low for k in
                                      ("fetching", "download", "installing",
                                       "refreshing", "warming")):
            self.connections += 1
        if any(k in low for k in ("download", "installing", "warming")) or \
                ("found " in low and "commit" in low):
            self.downloads += 1
        if not is_err:
            self._apply_stage(self._classify(low))
        if "update complete" in low:
            self.saw_complete = True
            m = re.search(r"\((v[^)]*→[^)]*)\)\s*(\[[^\]]*\])", line)
            self.version_line = (m.group(1) + " " + m.group(2)) if m else line
            self._force_complete()
        elif "code updated" in low:
            self._force_complete()
        if self.check_only:
            if "update available" in low:
                self.available_line = line
            if "up to date" in low:
                self.uptodate_line = line
        self._insert_log(line, "err" if is_err else None)
        if is_err and self.current_idx >= 0 and self.stage_status[self.current_idx] == "active":
            self.stage_status[self.current_idx] = "error"
            self._refresh_stages()
        self._update_counters()

    def _apply_stage(self, idx):
        if self.force_done or idx is None:
            return
        if idx < self.current_idx:
            return
        if idx == self.current_idx:
            if self.stage_status[idx] == "pending":
                self.stage_status[idx] = "active"
                self.log_gui(self.T("g_stage") % self.stage_name(idx))
                self._refresh_stages()
                self._update_header()
            return
        for j in range(self.current_idx + 1, idx):
            if self.stage_status[j] in ("pending", "active", "error"):
                self.stage_status[j] = "done"
        self.current_idx = idx
        self.stage_status[idx] = "active"
        self.log_gui(self.T("g_stage") % self.stage_name(idx))
        self._recompute_progress()
        self._refresh_stages()
        self._update_header()

    def _force_complete(self):
        self.force_done = True
        for j in range(len(STAGES)):
            self.stage_status[j] = "done"
        self.current_idx = len(STAGES) - 1
        self._set_progress(100.0)
        self._refresh_stages()
        self._update_header()

    def _recompute_progress(self):
        total = 0.0
        for i, st in enumerate(STAGES):
            s = self.stage_status[i]
            if s == "done":
                total += st["weight"]
            elif s in ("active", "error"):
                total += st["weight"] * 0.5
        self._set_progress(total)

    def _set_progress(self, value):
        self.progress = max(self.progress, min(100.0, value))
        self.progressbar["value"] = self.progress
        self.percent_label.config(text="%d%%" % int(self.progress))

    def _refresh_stages(self):
        for i, st in enumerate(STAGES):
            s = self.stage_status[i]
            row, icon, name = self.stage_rows[i]
            if s == "pending":
                icon.config(text=self.T("pending_word"), fg=GRAY)
                name.config(fg=GRAY)
                bg = PANEL
            elif s == "active":
                icon.config(text=SPINNER[self.spin_idx % len(SPINNER)], fg=ACCENT)
                name.config(fg=ACCENT)
                bg = HILITE
            elif s == "done":
                icon.config(text="✓", fg=SUCCESS)
                name.config(fg=FG)
                bg = PANEL
            else:
                icon.config(text="✗", fg=ERROR)
                name.config(fg=FG)
                bg = PANEL
            row.config(bg=bg)
            icon.config(bg=bg)
            name.config(bg=bg)
            name.config(text="%d. %s" % (i + 1, self.stage_name(i)))

    def _update_header(self):
        if self.current_idx >= 0:
            self.stage_header.config(text=self.stage_name(self.current_idx))
        else:
            self.stage_header.config(text=self.T("waiting"))

    def _update_counters(self):
        self.counters_label.config(
            text=self.T("counters") % (self.connections, self.downloads, self.errors))

    def _insert_log(self, text, tag):
        self.log_widget.configure(state="normal")
        self.log_widget.insert("end", text + "\n", (tag,) if tag else ())
        count = int(self.log_widget.index("end-1c").split(".")[0])
        if count > MAX_LOG_LINES:
            self.log_widget.delete("1.0", "%d.0" % (count - MAX_LOG_LINES + 1))
        self.log_widget.configure(state="disabled")
        self.log_widget.see("end")

    def write_log(self, line):
        try:
            self.log_f.write(line + "\n")
            self.log_f.flush()
        except OSError:
            pass

    def log_gui(self, text):
        line = text if text.startswith("[gui]") else "[gui] " + text
        self.write_log(line)
        self._insert_log(line, "gui")

    def _render_banner_text(self, key_or_text, args=None):
        if key_or_text in I18N[self.lang]:
            return self.T(key_or_text) % args if args else self.T(key_or_text)
        return key_or_text

    def _show_banner(self, color, title_key, specs):
        title = self._render_banner_text(title_key)
        details = [self._render_banner_text(*spec) if isinstance(spec, tuple)
                   else self._render_banner_text(spec) for spec in specs]
        self.banner_frame.grid(row=4, column=0, sticky="we", padx=10, pady=(4, 4))
        self.banner_frame.config(highlightbackground=color)
        self.banner_title.config(text=title, fg=color)
        self.banner_detail.config(text="\n".join(details))
        self.banner_state = (color, title_key, specs)

    def _on_exit(self, code):
        if not self.running:
            return
        self.running = False
        self.cancel_btn.config(state="disabled")
        if self.cancelled:
            self.log_gui(self.T("g_final_cancel"))
            self._show_banner(WARNING, "b_cancelled",
                              ["d_cancelled", ("d_log", (self.log_path,))])
        elif self.check_only and code == 0:
            if self.available_line:
                title_key, detail = "b_available", self.available_line
            elif self.uptodate_line:
                title_key, detail = "b_check_done", self.uptodate_line
            else:
                title_key, detail = "b_check_done", None
            self.log_gui(self.T("g_final_check") % code)
            self._show_banner(SUCCESS, title_key, [detail] if detail else [])
        elif code == 0 and self.saw_complete:
            self.log_gui(self.T("g_final_ok"))
            details = []
            if self.version_line:
                details.append(self.version_line)
            details.append("d_close")
            self._show_banner(SUCCESS, "b_complete", details)
        else:
            self.log_gui(self.T("g_final_err") % code)
            details = [("d_exit", (code,))]
            details.extend(self.error_lines[-5:])
            details.append(("d_log", (self.log_path,)))
            details.append("d_close_err")
            self._show_banner(ERROR, "b_aborted", details)
        self.open_log_btn.pack(side="right", padx=6)
        self.open_dir_btn.pack(side="right", padx=6)

    def cancel(self):
        if not self.running or self.cancelled:
            return
        self.cancelled = True
        self.log_gui(self.T("g_cancel"))
        self.cancel_btn.config(state="disabled")
        if self.proc is not None and self.proc.poll() is None:
            self.proc.terminate()
            # threading.Timer (not root.after): the kill must still happen if
            # the window is closed right after cancel.
            threading.Timer(3.0, self._kill_if_alive).start()

    def _kill_if_alive(self):
        try:
            if self.proc is not None and self.proc.poll() is None:
                self.proc.kill()
        except OSError:
            pass

    def open_log(self):
        try:
            os.startfile(self.log_path)
        except OSError:
            pass

    def open_hermes_dir(self):
        try:
            os.startfile(self.hermes_dir)
        except OSError:
            pass

    def on_close(self):
        self.log_gui(self.T("g_close"))
        if self.running:
            self.cancel()
            self.log_gui(self.T("g_final_cancel_close"))
        try:
            self.log_f.close()
        except OSError:
            pass
        self.root.destroy()


def show_already_running(lang):
    lang = lang if lang in I18N else detect_language()
    r = tk.Tk()
    r.title(I18N[lang]["lock_title"])
    r.geometry("440x150")
    r.configure(bg=BG)
    bar = tk.Frame(r, bg=BG)
    bar.pack(fill="x", padx=12, pady=(10, 0))
    tk.Button(bar, text=I18N[lang]["lang_button"],
              command=lambda: _swap_lock(r, lang),
              bg=PANEL, fg=ACCENT, activebackground=ACCENT, activeforeground=BG,
              font=("Segoe UI", 9, "bold"), relief="flat", width=4, padx=6, pady=2
              ).pack(side="right")
    tk.Label(r, text=I18N[lang]["lock_1"], bg=BG, fg=FG,
             font=("Segoe UI", 11)).pack(padx=16, pady=(14, 4))
    tk.Label(r, text=I18N[lang]["lock_2"], bg=BG, fg=GRAY,
             font=("Segoe UI", 10)).pack(padx=16, pady=(0, 14))
    r.mainloop()


def _swap_lock(root, lang):
    root.destroy()
    show_already_running("ru" if lang == "en" else "en")


def main():
    argv = sys.argv[1:]
    if "--version" in argv:
        print("hermes-alt-update-gui v%s" % VERSION)
        return 0
    lang = None
    if "--lang" in argv:
        i = argv.index("--lang")
        if i + 1 < len(argv) and argv[i + 1].lower() in I18N:
            lang = argv[i + 1].lower()
    lock = acquire_single_instance()
    if lock is None:
        # another copy is already running - do not start a second updater
        try:
            show_already_running(lang or saved_language())
        except Exception:
            pass
        return 0
    app = HermesUpdateGUI(argv)
    try:
        app.root.mainloop()
    except Exception:
        import traceback
        app.log_gui(app.T("g_traceback") + traceback.format_exc())
        raise
    finally:
        if lock not in (None, "ok"):
            try:
                ctypes.windll.kernel32.ReleaseMutex(lock)
                ctypes.windll.kernel32.CloseHandle(lock)
            except Exception:
                pass
    return 0


if __name__ == "__main__":
    main()
