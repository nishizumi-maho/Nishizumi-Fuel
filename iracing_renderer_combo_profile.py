#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

IRACING_DOCS = Path(r"C:\Users\user\Documents\iRacing")
PROFILE_ROOT = IRACING_DOCS / "combo_profiles"
APP_SETTINGS_PATH = PROFILE_ROOT / "app_settings.json"
MANIFEST_PATH = PROFILE_ROOT / "index.json"

RENDERER_OPTIONS = {
    "Monitor": "rendererDX11Monitor.ini",
    "OpenXR": "rendererDX11OpenXR.ini",
    "OpenVR": "rendererDX11OpenVR.ini",
}

GROUPING_OPTIONS = {
    "Car + track": "car_track",
    "Car": "car",
    "Track": "track",
    "SeriesID": "series",
    "SeriesID + track": "series_track",
}


def now_str() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


class ProfileStore:
    def __init__(self) -> None:
        PROFILE_ROOT.mkdir(parents=True, exist_ok=True)
        self.settings = self._load_json(APP_SETTINGS_PATH, default={})
        self.manifest = self._load_json(
            MANIFEST_PATH,
            default={"updated_at": now_str(), "renderers": {}},
        )

    @staticmethod
    def _load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
        if path.exists():
            try:
                loaded = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    return loaded
            except Exception:
                pass
        return default

    def save_settings(self) -> None:
        APP_SETTINGS_PATH.write_text(json.dumps(self.settings, indent=2), encoding="utf-8")

    def save_manifest(self) -> None:
        self.manifest["updated_at"] = now_str()
        MANIFEST_PATH.write_text(json.dumps(self.manifest, indent=2), encoding="utf-8")

    def selected_renderer(self) -> str:
        value = str(self.settings.get("default_renderer") or "rendererDX11OpenXR.ini")
        return value if value in RENDERER_OPTIONS.values() else "rendererDX11OpenXR.ini"

    def selected_grouping(self) -> str:
        value = str(self.settings.get("default_grouping") or "car_track")
        return value if value in GROUPING_OPTIONS.values() else "car_track"

    def set_renderer(self, renderer_file: str) -> None:
        self.settings["default_renderer"] = renderer_file
        self.save_settings()

    def set_grouping(self, grouping_mode: str) -> None:
        self.settings["default_grouping"] = grouping_mode
        self.save_settings()

    def list_entries(self, renderer_file: str, grouping_mode: str) -> list[dict[str, Any]]:
        renderers = self.manifest.get("renderers", {})
        renderer_section = renderers.get(renderer_file, {})
        groupings = renderer_section.get("groupings", {})
        grouping_section = groupings.get(grouping_mode, {})
        combos = grouping_section.get("combos", {})

        if not isinstance(combos, dict):
            return []

        entries = list(combos.values())
        entries.sort(
            key=lambda item: (
                str(item.get("track_display") or item.get("track_internal") or ""),
                str(item.get("track_config") or ""),
                str(item.get("car_screen") or item.get("car_path") or ""),
                str(item.get("series_id") or ""),
            )
        )
        return entries

    def update_combo_flags(
        self,
        renderer_file: str,
        grouping_mode: str,
        combo_key: str,
        *,
        enabled: bool,
        autosave_on_manual_close: bool,
    ) -> None:
        combos = (
            self.manifest.setdefault("renderers", {})
            .setdefault(renderer_file, {})
            .setdefault("groupings", {})
            .setdefault(grouping_mode, {})
            .setdefault("combos", {})
        )

        entry = combos.get(combo_key)
        if not isinstance(entry, dict):
            raise KeyError(combo_key)

        entry["enabled"] = bool(enabled)
        entry["autosave_on_manual_close"] = bool(autosave_on_manual_close)
        self.save_manifest()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.store = ProfileStore()
        self.setWindowTitle("iRacing Renderer Combo Profile Manager (PySide6)")
        self.resize(1020, 620)

        container = QWidget()
        root = QVBoxLayout(container)

        top_row = QGridLayout()
        top_row.addWidget(QLabel("Renderer:"), 0, 0)
        self.renderer_combo = QComboBox()
        for label, value in RENDERER_OPTIONS.items():
            self.renderer_combo.addItem(label, userData=value)
        top_row.addWidget(self.renderer_combo, 0, 1)

        top_row.addWidget(QLabel("Grouping:"), 0, 2)
        self.grouping_combo = QComboBox()
        for label, value in GROUPING_OPTIONS.items():
            self.grouping_combo.addItem(label, userData=value)
        top_row.addWidget(self.grouping_combo, 0, 3)

        self.refresh_btn = QPushButton("Refresh")
        self.open_folder_btn = QPushButton("Open combo_profiles")
        top_row.addWidget(self.refresh_btn, 0, 4)
        top_row.addWidget(self.open_folder_btn, 0, 5)

        root.addLayout(top_row)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Track", "Config", "Car", "Series", "Enabled", "Autosave", "Key"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        root.addWidget(self.table)

        actions = QHBoxLayout()
        self.enabled_chk = QCheckBox("Enabled")
        self.autosave_chk = QCheckBox("Autosave on close")
        self.save_flags_btn = QPushButton("Save selected flags")

        actions.addWidget(self.enabled_chk)
        actions.addWidget(self.autosave_chk)
        actions.addWidget(self.save_flags_btn)
        actions.addStretch(1)

        root.addLayout(actions)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Status log...")
        root.addWidget(self.log)

        self.setCentralWidget(container)

        self._wire_events()
        self._load_initial_selection()
        self.refresh_entries()

    def _wire_events(self) -> None:
        self.renderer_combo.currentIndexChanged.connect(self._on_renderer_changed)
        self.grouping_combo.currentIndexChanged.connect(self._on_grouping_changed)
        self.refresh_btn.clicked.connect(self.refresh_entries)
        self.open_folder_btn.clicked.connect(self.open_profile_folder)
        self.table.itemSelectionChanged.connect(self.sync_flags_from_row)
        self.save_flags_btn.clicked.connect(self.save_selected_flags)

    def _load_initial_selection(self) -> None:
        renderer = self.store.selected_renderer()
        grouping = self.store.selected_grouping()

        for i in range(self.renderer_combo.count()):
            if self.renderer_combo.itemData(i) == renderer:
                self.renderer_combo.setCurrentIndex(i)
                break

        for i in range(self.grouping_combo.count()):
            if self.grouping_combo.itemData(i) == grouping:
                self.grouping_combo.setCurrentIndex(i)
                break

    def _on_renderer_changed(self) -> None:
        renderer = self.current_renderer()
        if renderer:
            self.store.set_renderer(renderer)
            self.log_line(f"Renderer set to: {renderer}")
            self.refresh_entries()

    def _on_grouping_changed(self) -> None:
        grouping = self.current_grouping()
        if grouping:
            self.store.set_grouping(grouping)
            self.log_line(f"Grouping set to: {grouping}")
            self.refresh_entries()

    def current_renderer(self) -> str:
        return str(self.renderer_combo.currentData() or "")

    def current_grouping(self) -> str:
        return str(self.grouping_combo.currentData() or "")

    def refresh_entries(self) -> None:
        renderer = self.current_renderer()
        grouping = self.current_grouping()
        if not renderer or not grouping:
            return

        entries = self.store.list_entries(renderer, grouping)
        self.table.setRowCount(len(entries))

        for row, entry in enumerate(entries):
            track = str(entry.get("track_display") or entry.get("track_internal") or "-")
            cfg = str(entry.get("track_config") or "-")
            car = str(entry.get("car_screen") or entry.get("car_path") or "-")
            series = str(entry.get("series_id") or "-")
            enabled = "Yes" if bool(entry.get("enabled", True)) else "No"
            autosave = "Yes" if bool(entry.get("autosave_on_manual_close", True)) else "No"
            key = str(entry.get("combo_key") or "")

            self.table.setItem(row, 0, QTableWidgetItem(track))
            self.table.setItem(row, 1, QTableWidgetItem(cfg))
            self.table.setItem(row, 2, QTableWidgetItem(car))
            self.table.setItem(row, 3, QTableWidgetItem(series))
            self.table.setItem(row, 4, QTableWidgetItem(enabled))
            self.table.setItem(row, 5, QTableWidgetItem(autosave))
            self.table.setItem(row, 6, QTableWidgetItem(key))

        self.table.resizeColumnsToContents()
        self.log_line(f"Loaded {len(entries)} profile entries.")

    def current_combo_key(self) -> str:
        row = self.table.currentRow()
        if row < 0:
            return ""
        item = self.table.item(row, 6)
        return item.text().strip() if item else ""

    def sync_flags_from_row(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return

        enabled_item = self.table.item(row, 4)
        autosave_item = self.table.item(row, 5)
        self.enabled_chk.setChecked(bool(enabled_item and enabled_item.text() == "Yes"))
        self.autosave_chk.setChecked(bool(autosave_item and autosave_item.text() == "Yes"))

    def save_selected_flags(self) -> None:
        combo_key = self.current_combo_key()
        if not combo_key:
            QMessageBox.information(self, "No selection", "Select a profile row first.")
            return

        try:
            self.store.update_combo_flags(
                self.current_renderer(),
                self.current_grouping(),
                combo_key,
                enabled=self.enabled_chk.isChecked(),
                autosave_on_manual_close=self.autosave_chk.isChecked(),
            )
        except KeyError:
            QMessageBox.warning(self, "Missing entry", f"Combo key not found: {combo_key}")
            return

        self.log_line(
            f"Updated {combo_key}: enabled={self.enabled_chk.isChecked()} autosave={self.autosave_chk.isChecked()}"
        )
        self.refresh_entries()

    def open_profile_folder(self) -> None:
        PROFILE_ROOT.mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(PROFILE_ROOT))
            elif sys.platform == "darwin":
                subprocess.run(["open", str(PROFILE_ROOT)], check=False)
            else:
                subprocess.run(["xdg-open", str(PROFILE_ROOT)], check=False)
            self.log_line(f"Opened folder: {PROFILE_ROOT}")
        except Exception as exc:
            QMessageBox.warning(self, "Open folder failed", str(exc))

    def log_line(self, text: str) -> None:
        self.log.append(f"[{now_str()}] {text}")


def main() -> int:
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
