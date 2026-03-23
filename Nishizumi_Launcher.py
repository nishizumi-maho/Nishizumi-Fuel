#!/usr/bin/env python3
"""Unified launcher menu for the Nishizumi overlay apps.

This menu keeps each tool in its own process so the Tkinter- and PyQt-based
apps can run at the same time without fighting over a single UI event loop.
Users can open or close any supported app directly from the launcher.
"""

from __future__ import annotations

import subprocess
import sys
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import messagebox
from typing import Dict, Optional


BASE_DIR = Path(__file__).resolve().parent
APP_SCRIPTS = {
    "fuel": BASE_DIR / "Nishizumi_Fuel.py",
    "pittime": BASE_DIR / "Nishizumi_PitTime.py",
    "tirewear": BASE_DIR / "Nishizumi_TireWear (2).py",
    "traction": BASE_DIR / "Nishizumi_Traction.py",
}


@dataclass(frozen=True)
class AppDefinition:
    key: str
    title: str
    description: str
    script_path: Path


APP_DEFINITIONS = [
    AppDefinition(
        key="fuel",
        title="Fuel Overlay",
        description="Smart fuel monitoring, stint tracking, and lap targets.",
        script_path=APP_SCRIPTS["fuel"],
    ),
    AppDefinition(
        key="pittime",
        title="Pit Time Overlay",
        description="Pit loss calculations and race minimal rejoin safety view.",
        script_path=APP_SCRIPTS["pittime"],
    ),
    AppDefinition(
        key="tirewear",
        title="Tire Wear Overlay",
        description="Learns tire wear trends and shows overlay/help dialogs.",
        script_path=APP_SCRIPTS["tirewear"],
    ),
    AppDefinition(
        key="traction",
        title="Traction Overlay",
        description="Traction circle plus quickstart and coaching options.",
        script_path=APP_SCRIPTS["traction"],
    ),
]


class LauncherApp:
    POLL_INTERVAL_MS = 1000

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Nishizumi Tools Launcher")
        self.root.geometry("560x360")
        self.root.minsize(520, 320)
        self.root.configure(bg="#101317")

        self.processes: Dict[str, subprocess.Popen[str]] = {}
        self.status_vars: Dict[str, tk.StringVar] = {}
        self.button_vars: Dict[str, tk.StringVar] = {}

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(self.POLL_INTERVAL_MS, self._poll_processes)

    def _build_ui(self) -> None:
        outer = tk.Frame(self.root, bg="#101317", padx=18, pady=18)
        outer.pack(fill="both", expand=True)

        tk.Label(
            outer,
            text="Nishizumi Tools",
            font=("Segoe UI", 18, "bold"),
            fg="#e6f6e6",
            bg="#101317",
        ).pack(anchor="w")

        tk.Label(
            outer,
            text="Open or close each overlay from one menu. Each app runs in its own window/process.",
            font=("Segoe UI", 10),
            fg="#a6b3c2",
            bg="#101317",
            wraplength=520,
            justify="left",
        ).pack(anchor="w", pady=(4, 14))

        actions = tk.Frame(outer, bg="#101317")
        actions.pack(fill="x", pady=(0, 12))

        tk.Button(
            actions,
            text="Open all",
            command=self._open_all,
            font=("Segoe UI", 10, "bold"),
            bg="#243146",
            fg="#f5f7fa",
            relief="flat",
            padx=12,
            pady=6,
        ).pack(side="left")

        tk.Button(
            actions,
            text="Close all",
            command=self._close_all,
            font=("Segoe UI", 10),
            bg="#3b1f24",
            fg="#f5f7fa",
            relief="flat",
            padx=12,
            pady=6,
        ).pack(side="left", padx=(8, 0))

        self.summary_var = tk.StringVar(value="No overlays running.")
        tk.Label(
            outer,
            textvariable=self.summary_var,
            font=("Segoe UI", 10),
            fg="#8fd18f",
            bg="#101317",
        ).pack(anchor="w", pady=(0, 12))

        card_host = tk.Frame(outer, bg="#101317")
        card_host.pack(fill="both", expand=True)
        card_host.columnconfigure(0, weight=1)

        for row_index, app in enumerate(APP_DEFINITIONS):
            self._build_app_card(card_host, app, row_index)

        tk.Label(
            outer,
            text="Tip: you can still close any overlay from its own window; the launcher will notice automatically.",
            font=("Segoe UI", 9),
            fg="#7f8c99",
            bg="#101317",
            wraplength=520,
            justify="left",
        ).pack(anchor="w", pady=(12, 0))

        self._refresh_all_status_labels()

    def _build_app_card(self, parent: tk.Widget, app: AppDefinition, row_index: int) -> None:
        card = tk.Frame(parent, bg="#171c24", bd=1, highlightthickness=1, highlightbackground="#283241")
        card.grid(row=row_index, column=0, sticky="ew", pady=5)
        card.columnconfigure(0, weight=1)

        text_frame = tk.Frame(card, bg="#171c24", padx=12, pady=10)
        text_frame.grid(row=0, column=0, sticky="nsew")

        tk.Label(
            text_frame,
            text=app.title,
            font=("Segoe UI", 12, "bold"),
            fg="#f3f5f7",
            bg="#171c24",
        ).pack(anchor="w")

        tk.Label(
            text_frame,
            text=app.description,
            font=("Segoe UI", 9),
            fg="#a6b3c2",
            bg="#171c24",
            wraplength=330,
            justify="left",
        ).pack(anchor="w", pady=(2, 6))

        status_var = tk.StringVar(value="Status: Stopped")
        self.status_vars[app.key] = status_var
        tk.Label(
            text_frame,
            textvariable=status_var,
            font=("Segoe UI", 9),
            fg="#8fd18f",
            bg="#171c24",
        ).pack(anchor="w")

        controls = tk.Frame(card, bg="#171c24", padx=12, pady=10)
        controls.grid(row=0, column=1, sticky="ns")

        button_var = tk.StringVar(value="Open")
        self.button_vars[app.key] = button_var
        tk.Button(
            controls,
            textvariable=button_var,
            command=lambda key=app.key: self._toggle_app(key),
            width=10,
            font=("Segoe UI", 10, "bold"),
            bg="#243146",
            fg="#f5f7fa",
            relief="flat",
            padx=8,
            pady=8,
        ).pack()

    def _toggle_app(self, key: str) -> None:
        if self._is_running(key):
            self._stop_app(key)
        else:
            self._start_app(key)

    def _start_app(self, key: str) -> None:
        app = self._get_app_definition(key)
        if app is None:
            return
        if self._is_running(key):
            return
        if not app.script_path.exists():
            messagebox.showerror("Missing app", f"Could not find:\n{app.script_path}")
            return

        try:
            process = subprocess.Popen(
                [sys.executable, str(app.script_path)],
                cwd=str(BASE_DIR),
                text=True,
            )
        except OSError as exc:
            messagebox.showerror("Launch failed", f"Could not start {app.title}.\n\n{exc}")
            return

        self.processes[key] = process
        self._refresh_all_status_labels()

    def _stop_app(self, key: str) -> None:
        process = self.processes.get(key)
        if process is None:
            self._refresh_all_status_labels()
            return

        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)

        self.processes.pop(key, None)
        self._refresh_all_status_labels()

    def _open_all(self) -> None:
        for app in APP_DEFINITIONS:
            self._start_app(app.key)

    def _close_all(self) -> None:
        for app in list(APP_DEFINITIONS):
            self._stop_app(app.key)

    def _poll_processes(self) -> None:
        stale_keys = [key for key, process in self.processes.items() if process.poll() is not None]
        for key in stale_keys:
            self.processes.pop(key, None)
        self._refresh_all_status_labels()
        self.root.after(self.POLL_INTERVAL_MS, self._poll_processes)

    def _refresh_all_status_labels(self) -> None:
        running_titles = []
        for app in APP_DEFINITIONS:
            running = self._is_running(app.key)
            status = "Running" if running else "Stopped"
            self.status_vars[app.key].set(f"Status: {status}")
            self.button_vars[app.key].set("Close" if running else "Open")
            if running:
                running_titles.append(app.title)

        if running_titles:
            self.summary_var.set("Running: " + ", ".join(running_titles))
        else:
            self.summary_var.set("No overlays running.")

    def _is_running(self, key: str) -> bool:
        process = self.processes.get(key)
        return process is not None and process.poll() is None

    @staticmethod
    def _get_app_definition(key: str) -> Optional[AppDefinition]:
        for app in APP_DEFINITIONS:
            if app.key == key:
                return app
        return None

    def _on_close(self) -> None:
        if self.processes:
            should_close = messagebox.askyesno(
                "Close launcher",
                "Close the launcher and stop all running overlays?",
            )
            if not should_close:
                return
        self._close_all()
        self.root.destroy()

    def run(self) -> int:
        self.root.mainloop()
        return 0


def main() -> int:
    return LauncherApp().run()


if __name__ == "__main__":
    raise SystemExit(main())
