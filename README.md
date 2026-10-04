# Aceso

A MicroPython firmware for heart rate measurement device written in MicroPython. Aceso is a heart rate variability (HRV) measurement device that utilizes photoplethysmography (PPG). The device is built around a Raspberry Pi Pico W microcontroller paired with a Crowtail Pulse Sensor v2.0 for PPG signal detection, an SSD1306 OLED display for the user interface, and a rotary encoder as well as some buttons for navigation.

## Prerequisites

Install [mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html) on your system:

```bash
pip install mpremote
```

Connect your board via USB before running any commands.

## Installation

1. Make sure mpremote installed (look at Prerequistisites).
2. Make sure that your Raspberry Pi is:
   - Connected to your machine
   - Has MicroPython installed
   - Is not used by some other programs
3. Run install.sh for linux/macos or install.ps1 for Windows.

## Usage

- You can edit device's name, network's SSID and password in `config.py`.
- Device only works on 2.4 GHz network.

## Syncing files

Two sync utility scripts are provided — one for Linux/macOS and one for Windows.

### Linux / macOS

Make the script executable once:

```bash
chmod +x mpremote-sync.sh
```

**Push** local files to the board:

```bash
./mpremote-sync.sh push
```

**Push with a clean slate** — wipes the remote filesystem first, then pushes:

```bash
./mpremote-sync.sh push --clean
```

> ⚠️ **Warning:** This permanently deletes everything on the board's filesystem before pushing. Any files on the board that don't exist locally will be lost.

**Pull** all files from the board back to your current directory:

```bash
./mpremote-sync.sh pull
```

**Specify a port** if the board isn't auto-detected:

```bash
./mpremote-sync.sh push --port /dev/ttyUSB0
./mpremote-sync.sh push --clean --port /dev/cu.usbmodem1101
```

### Windows (PowerShell)

**Push** local files to the board:

```powershell
.\mpremote-sync.ps1 push
```

**Push with a clean slate** — wipes the remote filesystem first, then pushes:

```powershell
.\mpremote-sync.ps1 push -Clean
```

> ⚠️ **Warning:** This permanently deletes everything on the board's filesystem before pushing. Any files on the board that don't exist locally will be lost.

**Pull** all files from the board back to your current directory:

```powershell
.\mpremote-sync.ps1 pull
```

**Specify a port** if the board isn't auto-detected:

```powershell
.\mpremote-sync.ps1 push -Port COM3
.\mpremote-sync.ps1 push -Clean -Port COM3
```

## Typical workflow with Thonny IDE

1. Clone this repository on your development machine.
2. Push the files to the board:
   ```bash
   ./mpremote-sync.sh push        # Linux/macOS
   .\mpremote-sync.ps1 push       # Windows
   ```
3. Edit code in Thonny.
4. Once changes are ready, push back to the main machine:
   ```bash
   ./mpremote-sync.sh pull        # Linux/macOS
   .\mpremote-sync.ps1 pull       # Windows
   ```

> **Tip:** Use `--clean` / `-Clean` when you want to ensure the board's filesystem exactly mirrors your local copy, removing any files on the board that no longer exist locally.
