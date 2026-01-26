#!/usr/bin/env python3
"""Render a static overlay snapshot to validate sizing with large values."""

from __future__ import annotations

import tkinter as tk


WINDOW_WIDTH = 360
WINDOW_HEIGHT = 190


def main() -> None:
    root = tk.Tk()
    root.title("Fuel Consumption Monitor - Overlay Test")
    root.configure(bg="#0f1115")
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.attributes("-alpha", 0.92)

    top = tk.Frame(root, bg="#0f1115")
    top.pack(fill="x", padx=12, pady=(10, 4))

    avg_label = tk.Label(
        top,
        text="11.00 L/Lap",
        font=("Segoe UI", 20, "bold"),
        fg="#6fe38f",
        bg="#0f1115",
    )
    avg_label.pack(side="left")

    delta_label = tk.Label(
        top,
        text="(-11.20)",
        font=("Segoe UI", 14, "bold"),
        fg="#6fe38f",
        bg="#0f1115",
        padx=8,
    )
    delta_label.pack(side="left")

    bottom = tk.Frame(root, bg="#0f1115")
    bottom.pack(fill="x", padx=12, pady=(0, 6))

    tk.Label(
        bottom,
        text="Fuel: 55.00 L",
        font=("Segoe UI", 12),
        fg="#f2f2f2",
        bg="#0f1115",
    ).pack(anchor="w")

    tk.Label(
        bottom,
        text="Remaining: 5.0 laps",
        font=("Segoe UI", 12),
        fg="#f2f2f2",
        bg="#0f1115",
    ).pack(anchor="w")

    tk.Label(
        bottom,
        text="Last lap: 11.00 L",
        font=("Segoe UI", 12),
        fg="#f2f2f2",
        bg="#0f1115",
    ).pack(anchor="w")

    tk.Label(
        bottom,
        text="Stint: (C) 5; (E) 5",
        font=("Segoe UI", 12),
        fg="#d4d4d4",
        bg="#0f1115",
    ).pack(anchor="w")

    controls = tk.Frame(root, bg="#0f1115")
    controls.pack(fill="x", padx=12, pady=(0, 4))

    button_column = tk.Frame(controls, bg="#0f1115")
    button_column.pack(side="left", anchor="n", padx=(0, 8))

    button_row = tk.Frame(button_column, bg="#0f1115")
    button_row.pack(side="top")

    tk.Button(
        button_row,
        text="R",
        font=("Segoe UI", 8),
        bg="#1c2533",
        fg="#e8e8e8",
        relief="flat",
        padx=2,
        pady=0,
        width=1,
    ).pack(side="left", padx=(0, 4))

    tk.Button(
        button_row,
        text="I",
        font=("Segoe UI", 9),
        bg="#1c2533",
        fg="#e8e8e8",
        relief="flat",
        padx=6,
        pady=2,
        takefocus=False,
    ).pack(side="left")

    controls_body = tk.Frame(controls, bg="#0f1115")
    controls_body.pack(side="left", fill="x", expand=True)

    tk.Label(
        controls_body,
        text="Target L/Lap:",
        font=("Segoe UI", 10),
        fg="#c4c4c4",
        bg="#0f1115",
    ).pack(side="left")

    target_entry = tk.Entry(
        controls_body,
        width=6,
        font=("Segoe UI", 10),
        justify="center",
    )
    target_entry.insert(0, "22.20")
    target_entry.pack(side="left", padx=(6, 8))

    tk.Checkbutton(
        controls_body,
        text="Lock",
        font=("Segoe UI", 10),
        fg="#c4c4c4",
        bg="#0f1115",
        activebackground="#0f1115",
        selectcolor="#0f1115",
    ).pack(side="left")

    tk.Label(
        root,
        text="Test overlay: 11.00 L/lap, delta -11.20",
        font=("Segoe UI", 9),
        fg="#8c8c8c",
        bg="#0f1115",
    ).pack(anchor="w", padx=12, pady=(0, 6))

    root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+60+60")
    root.mainloop()


if __name__ == "__main__":
    main()
