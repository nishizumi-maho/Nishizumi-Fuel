# Nishizumi Tools

Nishizumi Tools is a collection of standalone iRacing helper overlays written in Python.
Each app solves a different race-day problem:

- **Fuel** helps you understand consumption, target saving, and estimated laps left.
- **PitTime** estimates your total pit loss and whether you will rejoin traffic safely.
- **TireWear** learns tire degradation for the current car/track combination over time.
- **Traction** shows how much grip you are using and points out where you are leaving time on the table.

The goal of this README is to explain the apps in plain language so a new user can install them, launch them, and understand what they are looking at without needing extra guidance.

---

## What you need before using any app

### 1. Required software

- **Windows** is the main intended platform because the tools store their data in `%APPDATA%\NishizumiTools` when available.
- **Python 3.10+**.
- **iRacing running with telemetry available**.
- The Python packages used by the tools:

```bash
pip install irsdk numpy pyqt5
```

Notes:
- `tkinter` is used by Fuel, PitTime, and Traction. It is included with most standard Python installs.
- `numpy` and `pyqt5` are required for TireWear.
- If you are on Linux/macOS, the apps fall back to `~/.config/NishizumiTools` for saved data instead of `%APPDATA%`.

### 2. Start order

For the smoothest experience:

1. Launch iRacing.
2. Join a session.
3. Click **Drive** so live telemetry is actually flowing.
4. Launch the app you want.

If an overlay says it is waiting for telemetry or disconnected, usually iRacing is open but you have not entered the car yet.

---

## Where the apps save data

Several tools remember their settings or learned values. They store them here:

- **Windows:** `%APPDATA%\NishizumiTools`
- **Fallback on other systems:** `~/.config/NishizumiTools`

Files currently used by this repo include:

- `fuel_consumption_monitor.json` - saved Fuel overlay position.
- `nishizumi_pittime_fuel_rates.json` - learned PitTime fuel rates and saved pit-loss profiles.
- `nishizumi_tirewear_model.json` - TireWear learned model data.
- `nishizumi_tirewear_settings.json` - TireWear overlay settings.

This means you can close and reopen the apps without losing everything every time.

---

## Included apps

## 1) Nishizumi FuelMonitor

**File:** `Nishizumi_FuelMonitor.py`

**Run:**
```bash
python Nishizumi_FuelMonitor.py
```

### What it does

Nishizumi FuelMonitor is a small always-on-top overlay that watches your live fuel use and turns it into simple race information:

- current average **fuel per lap**
- difference versus your manual target
- current fuel remaining
- estimated laps remaining
- last completed lap usage
- a comparison between your **planned stint** and your **estimated real stint**

It also detects pit entry/refueling behavior and can briefly switch to a large stint-average display while you are on pit road.

### What the overlay means

From top to bottom:

- **Large number** - your current average fuel consumption per lap.
- **Number in parentheses** - the delta versus the target you entered.
  - negative = you are saving more fuel than target
  - positive = you are using more fuel than target
- **Fuel** - how much fuel is currently in the car.
- **Remaining** - estimated laps left at the current average.
- **Last lap** - fuel used on the last valid completed lap.
- **Stint: (C) / (E)**
  - **(C)** = laps expected from the target consumption you typed in
  - **(E)** = laps estimated from your actual measured usage

### How to use it in a session

1. Start the app after entering the car in iRacing.
2. Drag the window to where you want it.
3. Watch a few green-flag laps so the app can build a useful average.
4. In **Target L/Lap**, type the fuel target you want to hit.
5. If you do not want to change the target by accident, click the checkbox to **lock** it.
6. Use the overlay during the run to see whether you are above or below target.

### Buttons and controls

- **R** - manually resets the current stint tracking.
  - Useful if the data became messy after unusual sim events or if you intentionally want to restart the calculation.
- **I** - toggles the advanced information panel.
- **Target field** - your planned fuel-per-lap target.
- **Lock checkbox** - freezes the target value and disables editing.

### Advanced panel explained

When you open the advanced panel, the app calculates **what would be required to gain or lose one lap of stint length**.

You will see two quick actions:

- **+1 lap** - automatically fills a more conservative target that should stretch the stint one lap further.
- **-1lap** - automatically fills a more aggressive target that spends fuel faster and shortens the stint by one lap.

This is useful when you want a fast answer to questions like:

- “How much do I need to save per lap to make this fuel number work?”
- “If I push harder, how much more fuel can I spend?”

### Important behavior to know

- The app ignores yellow/caution laps when building its stored lap history.
- It also rejects obviously anomalous lap values once it has enough history.
- It automatically adapts to **liters or gallons** based on iRacing display units.
- Entering pit road shows a temporary large **stint average** overlay for about 10 seconds.
- The overlay position is saved automatically when you move/close it.

### Best use case

Use Fuel during races where you need a quick answer to:

- whether you are on target
- how many laps you can realistically go
- whether one extra lap is possible with saving

---

## 2) Nishizumi Pittime

**File:** `Nishizumi_Pittime.py`

**Run:**
```bash
python Nishizumi_Pittime.py
```

### What it does

Nishizumi Pittime estimates two things in real time:

1. **How much total time your next pit stop will cost**.
2. **How safe your rejoin will be relative to traffic around you**.

It combines:

- a user-entered base pit loss
- optional tire-change time
- a learned or stored fueling rate
- current fuel in car and tank size
- nearby-car estimated time deltas from iRacing telemetry

### Main idea behind the calculation

The app computes:

**total pit loss = base pit loss + tire-change loss + fueling time**

Then it projects where you would rejoin relative to the cars around you and turns that into a simple status:

- **GREEN** - comfortable rejoin gap
- **YELLOW** - borderline
- **RED** - unsafe/tight rejoin

### How to set it up

In the **Pit loss setup** section:

- **Base pit loss (in + out, no service)**
  - Put the normal drive-through cost of pit entry and exit for the track.
- **Tire-change loss**
  - Put the extra time caused by changing tires.
- **Fuel rate [L/s] (auto-learned)**
  - The app learns this automatically when it observes you refueling on pit road.
- **Use custom fuel tank max [L]**
  - Enable this only if the telemetry-reported tank limit is wrong for your use case, or if you want to simulate a capped fill.
- **Custom fuel max [L]**
  - The tank size to use when the custom option is enabled.
- **Lock typed inputs (read-only)**
  - Prevent accidental edits while racing.
- **Race minimal mode**
  - Shrinks the app down to the rejoin safety section only.

### What the live output means

- **Fuel** - current fuel, detected max tank, and how much must be added to fill.
- **Fuel time** - how long the fill should take using the learned/stored fuel rate.
- **Total pit time loss** - complete stop cost based on your current settings.
- **Window** - a simple score and traffic status color.
- **Projected rejoin gaps** - estimated front and rear traffic gaps after applying the stop loss.

### How to use it in practice

1. Launch the app while in an iRacing session.
2. Enter or fine-tune your **base pit loss** for the current track.
3. If your series changes tires, enter the tire-change loss.
4. Let the app watch one real pit stop so it can auto-learn the fuel rate.
5. During the race, check the rejoin score before deciding whether to pit now or wait.
6. Use **minimal mode** if you only want the high-value traffic window display during green-flag racing.

### Profile saving behavior

PitTime automatically remembers setup values **per car and track**.
That means when you return to the same combination, it can restore:

- learned fuel rate
- base pit loss
- tire loss
- custom tank max

This is especially helpful if you run the same combo across multiple sessions or race weekends.

### Good workflow suggestion

- Practice session: do one or two pit stops so the fuel rate gets learned.
- Before the race: confirm the base pit loss and tire loss.
- During the race: use the color status and projected front/rear gaps to decide whether the current lap is a safe stop window.

---

## 3) Nishizumi TireWear

**File:** `Nishizumi_TireWear.py`

**Run:**
```bash
python "Nishizumi_TireWear.py"
```

### What it does

TireWear is a transparent overlay plus a background learning model.
It watches complete stints, learns how quickly your tires wear for a specific **car + track + configuration**, and then estimates remaining tread live while you drive.

Unlike a simple static tire display, this app tries to learn from:

- track temperature
- air temperature
- humidity
- driving load / energy per lap
- your completed stint history for the same combo

### What you see on the overlay

The HUD displays:

- **LF / RF / LR / RR tread percentages**
- **Track and config name**
- **Car identifier**
- **Model confidence**
- **SDK online/offline state**

Tire colors indicate rough condition:

- **green** - healthy tread
- **yellow** - moderate wear
- **red** - heavy wear / caution zone

### How the learning works

The app does not magically know your tire wear immediately.
It needs completed stint data.

A simplified workflow is:

1. Start a stint.
2. Drive normal laps.
3. Return to pit road.
4. The app compares start-of-stint wear to end-of-stint wear.
5. It stores that sample under the current car/track/config.
6. Future runs on the same combo become more accurate.

### Why model confidence matters

The overlay shows **model confidence** because predictions are only as good as the saved history.

- Low confidence = not enough completed learning samples yet.
- Higher confidence = the app has seen enough stints to make more trustworthy estimates.

If the app records data that looks like an outlier, it can reject that sample instead of poisoning the model.

### Built-in overlay controls

At the top-right of the overlay there are three buttons:

- **ℹ** - opens the information dialog.
  - Shows connection state, dataset key, temperatures, humidity, sample count, model confidence, and the current model coefficients.
- **⚙** - opens settings.
  - Lets you change always-on-top behavior, overlay opacity, font size, width, and height.
- **✕** - closes the overlay.

### Quick start inside the app

The app includes its own quick-start guide in the settings menu. The intended usage is:

1. Launch iRacing and join a session.
2. Start the app.
3. Drag the overlay where you want it.
4. Open Settings if you want to change size, opacity, or font.
5. Drive clean laps and complete stints so the model can learn.
6. Open the info dialog to inspect sample count and model confidence.
7. Only use **Reset data** if you really want to erase the learned history.

### Reset data button

The settings dialog includes **Reset data (clear memory)**.
Use it carefully.

It clears:

- the saved tire wear model file
- temporary runtime learning state for the current session

Use this when:

- you want to start the learning process from zero
- saved data became invalid
- you intentionally changed your workflow and want a fresh dataset

### Best use case

TireWear is best for longer runs and endurance practice where you want to answer questions like:

- which tire is wearing fastest on this combo?
- how much confidence should I have in the tire prediction?
- are the current conditions harder on tires than previous runs?

---

## 4) Nishizumi Traction

**File:** `Nishizumi_Traction.py`

**Run:**
```bash
python Nishizumi_Traction.py
```

### What it does

Traction is a coaching overlay built around a live **traction circle**.
It measures longitudinal and lateral acceleration, estimates your current grip usage, and then tries to identify parts of the lap where you are not reaching your learned reference level.

In plain language: it helps answer **“where am I leaving grip on the table?”**

### Main screen sections

- **Status row**
  - connection state
  - reminder that **M** toggles compact/detailed mode
  - buttons to load an IBT reference, return to live reference, and show/hide quickstart
- **Quickstart panel**
  - short guide for first-time users
- **Coaching settings**
  - number of laps needed before tips begin
  - whether only incident-free laps count
- **Traction circle**
  - live dot showing current combined braking/acceleration/cornering load
- **Telemetry summary**
  - current long/lat/total g
  - estimated grip limit
  - coaching quality metrics
  - generated coaching advice

### How the app learns a reference

By default, Traction builds a **live adaptive reference** from your own laps.

It divides the lap into many small segments and stores the best grip usage seen in each segment, while also filtering out outliers.
Then it compares your recent laps against that learned reference.

This means the coaching becomes better after you have driven a few representative laps.

### Incident-free laps option

The checkbox **Only count incident-free laps for learning and tips** is important.

- Enabled: the app ignores laps where you went off track when building coaching reference.
- Disabled: every completed lap can contribute.

If you want cleaner coaching, leave it enabled.
If you want feedback faster during testing, disable it.

### Tips threshold

The spinbox **Start tips after this many laps** controls when the app starts giving coaching advice.

Example:
- set it to **5**
- drive 5 valid/incident-free laps
- the app begins comparing your recent pace against the learned baseline

### Understanding the coaching output

The summary highlights the biggest grip deficits first.
For each improvement area it can tell you:

- where in the lap the issue appears
- the grip difference (**Δg**) between your current pace and the reference
- whether it looks like **entry**, **mid-corner**, or **exit** underuse
- whether the trend is improving, stable, or declining
- how often the issue appears across recent laps
- what to try next lap

Compact mode gives the most important advice only.
Detailed mode expands the breakdown.

### Keyboard shortcut

- Press **M** to switch between **compact** and **detailed** coaching summaries.

### Using an IBT file as reference

Traction can also use an external `.ibt` telemetry file instead of learning only from your current live session.

Buttons:

- **Load IBT** - choose an iRacing telemetry file and build a reference from it.
- **Use Live** - discard the IBT reference and return to the live adaptive reference.

This is useful if you want to compare yourself against:

- an earlier personal best
- a strong benchmark session
- a saved telemetry run from the same combo

### Best workflow

1. Launch the app after entering the car.
2. Leave quickstart visible if this is your first time.
3. Set how many laps should be required before coaching begins.
4. Decide whether only incident-free laps should count.
5. Drive several representative laps.
6. Read the top coaching items and try one change at a time.
7. Press **M** if you want the full detailed explanation.
8. Optionally load an `.ibt` file to compare against a stronger benchmark.

---

## Which app should I use?

Use this quick chooser:

- **I want to save fuel or know whether I can make another lap.** → **Fuel**
- **I want to know whether pitting now will rejoin into traffic.** → **PitTime**
- **I want to understand long-run tire degradation.** → **TireWear**
- **I want driving/coaching feedback about grip usage and lap execution.** → **Traction**

You can also run more than one overlay at the same time if your system and workflow are comfortable with it.

---

## Common troubleshooting

### The app says it is disconnected or waiting for telemetry

Usually one of these is true:

- iRacing is not running
- you joined a session but have not clicked **Drive** yet
- the telemetry is not available to `irsdk`

Fix:

1. open iRacing
2. join a session
3. click **Drive**
4. relaunch the app if needed

### A tool is not remembering data

Check whether the AppData folder exists:

- `%APPDATA%\NishizumiTools`

If the folder cannot be written, settings/model persistence may fail.

### TireWear predictions look weak at first

That is normal.
The app needs completed stints on the same combo before confidence improves.

### Fuel numbers look strange after a pit stop or caution-heavy run

Use the **R** reset button in Fuel if the current stint should be recalculated from scratch.

### PitTime fuel rate is wrong

Do one complete normal refueling stop and let the app relearn the value.
Because the rate is saved per car/track, old saved profiles may still be influencing the display until a new stop is observed.

### Traction coaching is not giving useful tips yet

Make sure you have:

- enough laps collected for the threshold you chose
- enough clean laps if incident-free mode is enabled
- representative pace rather than in/out laps

---

## Repository files

Current top-level files in this repo:

- `README.md`
- `Nishizumi_FuelMonitor.py`
- `Nishizumi_Pittime.py`
- `Nishizumi_TireWear.py`
- `Nishizumi_Traction.py`

---

## Final note

These are **standalone overlays**, not one monolithic app.
Pick the one that matches the problem you are trying to solve in that session, and let it learn over time where applicable.

If you are new to the collection, a simple order to try them is:

1. **Fuel** for immediate race usefulness
2. **PitTime** for strategy timing
3. **Traction** for driving improvement
4. **TireWear** for longer-run learning and endurance prep
