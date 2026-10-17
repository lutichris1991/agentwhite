# AgentWhite

AgentWhite is a local-first wireless and device security validation console for networks and hardware you own or are explicitly authorized to test.

The goal is simple: **discover -> enroll -> validate -> show proof -> explain impact -> patch -> retest**.

## What v0.1 does

- Runs entirely on `127.0.0.1` with no cloud requirement.
- Discovers nearby Wi-Fi networks using native OS tooling.
- Inventories Bluetooth hardware visible to the host OS.
- Inventories LAN neighbors from the local ARP/neighbor table.
- Requires explicit device enrollment before active validation.
- Probes a conservative set of common TCP services on enrolled LAN devices.
- Records findings/evidence locally in SQLite.
- Gives plain-English remediation guidance for confirmed exposure.
- Lets you open verified HTTP/HTTPS services directly from the device card.
- Includes an optional local-AI analyst integration for Ollama; it automatically falls back to deterministic offline analysis when Ollama is unavailable.

## Agent army

AgentWhite is organized around specialized agents:

- **Supervisor Agent** — enforces scope and coordinates work.
- **Recon Agent** — Wi-Fi, Bluetooth, and LAN discovery.
- **Verification Agent** — independently confirms observable access/exposure.
- **AccessScope Agent** — maps which services/resources are actually reachable at the achieved access level.
- **Evidence Agent** — stores reproducible evidence and timestamps.
- **Remediation Agent** — explains why the finding matters and how to close it.
- **Retest Agent** — re-runs the same validation after a fix.

Future active-test modules plug into the same enrollment and evidence controls. The core intentionally does not include indiscriminate credential attacks, destructive payloads, or automatic testing of unenrolled targets.

## Windows quick start

Requirements: Windows 10/11 and Python 3.11+.

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install_windows.ps1
```

Then launch **AgentWhite** from the Start Menu, or run:

```powershell
.\run_agentwhite.bat
```

The browser opens to `http://127.0.0.1:8765`.

## Run directly

```bash
python -m agentwhite.server
```

No third-party Python packages are required for the base application.

## Linux notes

AgentWhite uses `nmcli` for Wi-Fi discovery when available, `bluetoothctl` for Bluetooth inventory, and `ip neigh` for LAN neighbors.

```bash
python3 -m agentwhite.server
```

## Optional offline AI

If Ollama is installed locally and already has a model downloaded, AgentWhite can use it without Internet access. Set a preferred model with:

```powershell
$env:AGENTWHITE_MODEL="llama3.2:3b"
```

If no local model is available, AgentWhite continues to work normally with its built-in analysis rules.

## Scope model

Passive discovery can list devices/networks visible to the host. **Active validation is disabled until a target is explicitly enrolled in AgentWhite.** The enrollment state is stored locally and displayed prominently in the UI.

## Data location

Windows:

`%LOCALAPPDATA%\AgentWhite\agentwhite.db`

Linux/macOS:

`~/.agentwhite/agentwhite.db`

## Current milestone

v0.1 is the foundation: reliable discovery, explicit scope, evidence, service verification, remediation, and offline operation. The next milestone is hardware-adapter support (monitor-mode Wi-Fi/BLE), richer protocol-specific validators, PCAP evidence capture, and the verified-access viewer.