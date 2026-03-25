#!/usr/bin/env python3
"""Simple iRacing pit-service overlay with fueling vs tire-time planner."""

from __future__ import annotations

import time
import tkinter as tk
from typing import Optional

import irsdk

UPDATE_MS = 120
DEFAULT_FUEL_RATE_LPS = 2.0
DEFAULT_TIRE_SERVICE_S = 8.0
DEFAULT_TANK_CAPACITY_L = 120.0


def _safe_float(value: object) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


class PitServiceOverlay:
    BG = "#0f1115"
    PANEL = "#1a1f2b"
    PANEL_ALT = "#141824"
    TEXT = "#f3f4f6"
    MUTED = "#9ca3af"
    ACCENT = "#7dd3fc"
    GOOD = "#22c55e"
    WARN = "#f59e0b"

    def __init__(self) -> None:
        self.ir = irsdk.IRSDK()

        self.root = tk.Tk()
        self.root.title("Nishizumi Pit Service")
        self.root.configure(bg=self.BG)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.96)
        self.root.geometry("440x410+120+120")

        self._drag_x = 0
        self._drag_y = 0

        self.connected_var = tk.StringVar(value="Conectando ao iRacing…")
        self.session_var = tk.StringVar(value="Status: aguardando")
        self.pit_time_var = tk.StringVar(value="Tempo atual no box: --")
        self.last_pit_var = tk.StringVar(value="Último pit total: --")
        self.live_fuel_var = tk.StringVar(value="Combustível atual: --")
        self.rate_var = tk.StringVar(value=f"Taxa combustível: {DEFAULT_FUEL_RATE_LPS:.2f} L/s")

        self.tank_capacity_var = tk.StringVar(value=f"{DEFAULT_TANK_CAPACITY_L:.1f}")
        self.current_fuel_var = tk.StringVar(value="")
        self.target_fuel_var = tk.StringVar(value="100.0")
        self.tire_service_var = tk.StringVar(value=f"{DEFAULT_TIRE_SERVICE_S:.1f}")
        self.target_stop_time_var = tk.StringVar(value="12.0")

        self.summary_var = tk.StringVar(value="Planejamento aguardando dados...")
        self.min_fuel_var = tk.StringVar(value="Litros mínimos sem esperar pneus: --")
        self.stop_projection_var = tk.StringVar(value="Projeção de parada: --")
        self.time_solver_var = tk.StringVar(value="Litros para tempo alvo: --")

        self._in_pit = False
        self._pit_start_ts: Optional[float] = None
        self._last_pit_duration_s: Optional[float] = None

        self._last_tick_ts: Optional[float] = None
        self._last_fuel_l: Optional[float] = None
        self._fuel_rate_lps: float = DEFAULT_FUEL_RATE_LPS

        self._build_ui()
        self._loop()

    def _build_ui(self) -> None:
        shell = tk.Frame(self.root, bg=self.BG, highlightthickness=1, highlightbackground="#334155")
        shell.pack(fill="both", expand=True)

        title = tk.Frame(shell, bg=self.BG)
        title.pack(fill="x", padx=8, pady=(6, 4))
        title.bind("<ButtonPress-1>", self._start_move)
        title.bind("<B1-Motion>", self._on_move)

        tk.Label(title, text="Pit Service Overlay", bg=self.BG, fg=self.ACCENT, font=("Segoe UI", 11, "bold")).pack(side="left")
        tk.Button(title, text="✕", command=self.root.destroy, bg="#1f2937", fg=self.TEXT, relief="flat", padx=6).pack(side="right")

        live = tk.Frame(shell, bg=self.PANEL_ALT, padx=10, pady=8, highlightthickness=1, highlightbackground="#374151")
        live.pack(fill="x", padx=8, pady=(0, 8))

        for var, size, color in (
            (self.connected_var, 9, self.MUTED),
            (self.session_var, 10, self.TEXT),
            (self.pit_time_var, 14, "white"),
            (self.last_pit_var, 10, self.TEXT),
            (self.live_fuel_var, 10, self.TEXT),
            (self.rate_var, 10, self.ACCENT),
        ):
            tk.Label(live, textvariable=var, bg=self.PANEL_ALT, fg=color, anchor="w", font=("Segoe UI", size, "bold" if size >= 10 else "normal")).pack(fill="x")

        planner = tk.Frame(shell, bg=self.PANEL, padx=10, pady=8, highlightthickness=1, highlightbackground="#374151")
        planner.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self._entry_row(planner, "Tanque total [L]", self.tank_capacity_var, 0)
        self._entry_row(planner, "Combustível atual [L] (vazio = telemetria)", self.current_fuel_var, 1)
        self._entry_row(planner, "Litros para abastecer [L]", self.target_fuel_var, 2)
        self._entry_row(planner, "Tempo serviço pneus [s]", self.tire_service_var, 3)
        self._entry_row(planner, "Tempo de box alvo [s]", self.target_stop_time_var, 4)

        tk.Label(planner, textvariable=self.summary_var, bg=self.PANEL, fg=self.TEXT, anchor="w", justify="left", wraplength=400, font=("Segoe UI", 9, "bold")).grid(row=5, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        tk.Label(planner, textvariable=self.min_fuel_var, bg=self.PANEL, fg=self.GOOD, anchor="w", font=("Segoe UI", 9, "bold")).grid(row=6, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        tk.Label(planner, textvariable=self.stop_projection_var, bg=self.PANEL, fg=self.WARN, anchor="w", font=("Segoe UI", 9)).grid(row=7, column=0, columnspan=2, sticky="ew", pady=(2, 0))
        tk.Label(planner, textvariable=self.time_solver_var, bg=self.PANEL, fg=self.ACCENT, anchor="w", font=("Segoe UI", 9)).grid(row=8, column=0, columnspan=2, sticky="ew", pady=(2, 0))

        for i in range(2):
            planner.grid_columnconfigure(i, weight=1 if i == 1 else 0)

    def _entry_row(self, parent: tk.Widget, label: str, var: tk.StringVar, row: int) -> None:
        tk.Label(parent, text=label, bg=self.PANEL, fg=self.MUTED, anchor="w", font=("Segoe UI", 9)).grid(row=row, column=0, sticky="w", pady=2, padx=(0, 8))
        tk.Entry(parent, textvariable=var, bg="#0b1220", fg=self.TEXT, insertbackground=self.TEXT, relief="flat", font=("Segoe UI", 9)).grid(row=row, column=1, sticky="ew", pady=2)

    def _start_move(self, event: tk.Event) -> None:
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_move(self, event: tk.Event) -> None:
        self.root.geometry(f"+{event.x_root - self._drag_x}+{event.y_root - self._drag_y}")

    def _loop(self) -> None:
        now = time.time()
        if self.ir.startup():
            self.connected_var.set("Conectado ao iRacing")
            on_pit = bool(self.ir["OnPitRoad"] or False)
            fuel_level = _safe_float(self.ir["FuelLevel"])

            self._update_pit_state(on_pit, now)
            self._update_fuel_rate(on_pit, fuel_level, now)
            self._update_live_labels(on_pit, fuel_level)
            self._update_projection(fuel_level)
        else:
            self.connected_var.set("iRacing desconectado")
            self.session_var.set("Status: aguardando telemetria")
            self.pit_time_var.set("Tempo atual no box: --")

        self.root.after(UPDATE_MS, self._loop)

    def _update_pit_state(self, on_pit: bool, now: float) -> None:
        if on_pit and not self._in_pit:
            self._in_pit = True
            self._pit_start_ts = now

        if not on_pit and self._in_pit:
            self._in_pit = False
            if self._pit_start_ts is not None:
                self._last_pit_duration_s = max(0.0, now - self._pit_start_ts)
            self._pit_start_ts = None

    def _update_fuel_rate(self, on_pit: bool, fuel_level: Optional[float], now: float) -> None:
        if self._last_tick_ts is None or fuel_level is None or self._last_fuel_l is None:
            self._last_tick_ts = now
            self._last_fuel_l = fuel_level
            return

        dt = now - self._last_tick_ts
        if dt <= 0:
            return

        d_fuel = fuel_level - self._last_fuel_l
        if on_pit and d_fuel > 0.01:
            inst_rate = d_fuel / dt
            if 0.2 <= inst_rate <= 12.0:
                self._fuel_rate_lps = (self._fuel_rate_lps * 0.8) + (inst_rate * 0.2)

        self._last_tick_ts = now
        self._last_fuel_l = fuel_level

    def _update_live_labels(self, on_pit: bool, fuel_level: Optional[float]) -> None:
        if on_pit:
            self.session_var.set("Status: em pit lane")
            if self._pit_start_ts is not None:
                self.pit_time_var.set(f"Tempo atual no box: {time.time() - self._pit_start_ts:0.2f}s")
        else:
            self.session_var.set("Status: pista")
            self.pit_time_var.set("Tempo atual no box: --")

        if self._last_pit_duration_s is not None:
            self.last_pit_var.set(f"Último pit total (entrada até saída): {self._last_pit_duration_s:0.2f}s")

        if fuel_level is None:
            self.live_fuel_var.set("Combustível atual: --")
        else:
            self.live_fuel_var.set(f"Combustível atual: {fuel_level:0.2f} L")
            if not self.current_fuel_var.get().strip():
                self.current_fuel_var.set(f"{fuel_level:.2f}")

        self.rate_var.set(f"Taxa combustível: {self._fuel_rate_lps:0.2f} L/s")

    def _update_projection(self, telemetry_fuel: Optional[float]) -> None:
        tank = self._parse_or_default(self.tank_capacity_var.get(), DEFAULT_TANK_CAPACITY_L)
        tire_time = self._parse_or_default(self.tire_service_var.get(), DEFAULT_TIRE_SERVICE_S)
        fuel_to_add = max(0.0, self._parse_or_default(self.target_fuel_var.get(), 0.0))
        target_stop_time = max(0.0, self._parse_or_default(self.target_stop_time_var.get(), 0.0))

        current_fuel_input = self.current_fuel_var.get().strip()
        current_fuel = self._parse_or_default(current_fuel_input, telemetry_fuel or 0.0)
        current_fuel = max(0.0, min(current_fuel, tank))

        room_left = max(0.0, tank - current_fuel)
        fuel_to_add = min(fuel_to_add, room_left)

        fuel_time = fuel_to_add / max(self._fuel_rate_lps, 0.01)
        total_service_time = max(fuel_time, tire_time)
        wait_for_tire_s = max(0.0, tire_time - fuel_time)
        wait_for_fuel_s = max(0.0, fuel_time - tire_time)

        min_liters_no_tire_wait = min(room_left, tire_time * self._fuel_rate_lps)
        liters_for_target_time = min(room_left, target_stop_time * self._fuel_rate_lps)
        projected_for_target = max(target_stop_time, tire_time)

        self.summary_var.set(
            f"Abastecer {fuel_to_add:.1f} L => combustível {fuel_time:.2f}s | serviço total {total_service_time:.2f}s"
        )
        self.min_fuel_var.set(
            f"Litros mínimos sem esperar pneus: {min_liters_no_tire_wait:.1f} L"
        )

        if wait_for_tire_s > 0.05:
            self.stop_projection_var.set(
                f"Combustível termina ANTES dos pneus (+{wait_for_tire_s:.2f}s de espera dos pneus)."
            )
        elif wait_for_fuel_s > 0.05:
            self.stop_projection_var.set(
                f"Pneus terminam antes; abastecimento adiciona +{wait_for_fuel_s:.2f}s ao box."
            )
        else:
            self.stop_projection_var.set("Pneus e abastecimento terminam praticamente juntos.")

        self.time_solver_var.set(
            f"Para alvo de {target_stop_time:.1f}s: ~{liters_for_target_time:.1f} L (pit total projetado {projected_for_target:.1f}s+)."
        )

    def _parse_or_default(self, value: str, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default


if __name__ == "__main__":
    try:
        PitServiceOverlay().root.mainloop()
    except KeyboardInterrupt:
        pass
