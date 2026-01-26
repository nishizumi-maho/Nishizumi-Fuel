# Nishizumi Fuel

Nishizumi Fuel is a lightweight Tkinter overlay that monitors fuel usage in iRacing and
surfaces live fuel-per-lap, remaining laps, and stint planning insights. It listens to iRacing
telemetry via the `irsdk` Python bindings and keeps a small always-on-top window you can drag
around your screen.

## Features

- Live fuel-per-lap average with delta vs. target.
- Remaining laps estimate based on current fuel usage.
- Stint planning with planned vs. expected laps.
- Advanced insights for +1/-1 lap targets and per-lap savings.
- Automatic refuel detection and stint reset.
- Persists window position between launches.

## Requirements

- Python 3.10+
- iRacing running with telemetry enabled
- `irsdk` Python package available in your environment

## Quick start

```bash
python Nishizumi_Fuel.py
```

Launch iRacing first, then run the script. The overlay waits for telemetry and updates once
it detects live data.

## Controls

- **Drag**: Click-and-drag the window background to reposition it.
- **Target L/Lap**: Set a fuel-per-lap target for stint planning.
- **Lock**: Freeze the target value and prevent dragging via the window.
- **Reset**: Clear stint tracking and averages.
- **Insights**: Expand advanced stint planning details.

## Configuration & files

- Window position is saved to `~/.fuel_consumption_monitor.json` on close.
- Telemetry is read from iRacing session data; no additional config files are required.

## Documentation

For detailed behavior, telemetry sources, and calculation notes, see
[`DOCUMENTATION.md`](DOCUMENTATION.md).

## Repository structure

- `Nishizumi_Fuel.py`: Main Tkinter overlay and telemetry logic.
- `README.md`: Project overview and usage.
- `DOCUMENTATION.md`: Detailed technical documentation.
