# AgentWhite

AgentWhite is a local-first wireless and device security validation console for networks and hardware you own or are explicitly authorized to test.

The workflow is proof-first:

**discover -> enroll -> validate -> inspect returned access -> record evidence -> analyze -> patch -> retest**

## What v0.2 does

- Runs on `127.0.0.1` with no cloud requirement.
- Discovers nearby Wi-Fi networks using native OS tooling.
- Inventories LAN neighbors from the local ARP/neighbor table.
- Discovers Bluetooth/BLE devices through Bleak when available, with native OS inventory as a fallback.
- Requires explicit target enrollment before active validation or post-access inspection.
- Probes a conservative set of common TCP services on enrolled private/local LAN devices.
- Provides an **HTTP Verified Access Viewer** that retrieves an explicitly selected path from an enrolled HTTP/HTTPS service and shows returned text, images, or bounded binary evidence.
- Saves retrieved HTTP evidence locally and records SHA-256 hashes.
- Provides a **Bluetooth Proof-of-Access Viewer** that establishes a session to an enrolled BLE device, enumerates GATT services/characteristics, and reads characteristics the device exposes as readable.
- Records findings and remediation guidance locally in SQLite.
- Includes an **AI Analyst** page that can use a locally installed Ollama model to analyze the evidence already collected by AgentWhite.
- Falls back to deterministic offline analysis when no local AI model is available.

The v0.2 BLE inspector is non-destructive: it does not write GATT characteristics. AgentWhite also does not automatically test targets that have not been enrolled.

## Agent army

AgentWhite is organized around specialized agents:

- **Supervisor Agent** — enforces scope and coordinates work.
- **Recon Agent** — Wi-Fi, Bluetooth, and LAN discovery.
- **Verification Agent** — independently confirms observable exposure.
- **AccessScope Agent** — maps reachable services and inspects what an established authorized session actually exposes.
- **Evidence Agent** — stores reproducible evidence, timestamps, and hashes.
- **Remediation Agent** — explains why a finding matters and how to close it.
- **Retest Agent** — repeats validation after fixes.
- **AI Analyst** — performs evidence-grounded analysis with a local Ollama model when available.

## Windows installation

### Option 1: standalone Windows build

The repository includes `.github/workflows/build-windows.yml`. The workflow builds `AgentWhite.exe` with Bluetooth support bundled and uploads `AgentWhite-Windows.zip` as a GitHub Actions artifact.

After the executable is downloaded, normal AgentWhite operation is local/offline.

### Option 2: install from the repository

Requirements: Windows 10/11 and Python 3.11+.

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install_windows.ps1
```

The installer creates an isolated Python environment under `%LOCALAPPDATA%\AgentWhite`, installs Bluetooth support when available, creates a Start Menu shortcut, and launches AgentWhite.

The browser opens to:

`http://127.0.0.1:8765`

## Run directly

Base application:

```bash
python -m agentwhite.server
```

For BLE discovery and the Bluetooth Proof-of-Access Viewer:

```bash
pip install -e ".[bluetooth]"
python -m agentwhite.server
```

## Using the proof viewers

### LAN / HTTP

1. Scan LAN devices.
2. Enroll a device you are authorized to test.
3. Click **Verify Services**.
4. On a verified HTTP/HTTPS finding, click **View Returned Material**.
5. Enter the resource path you want AgentWhite to retrieve.
6. AgentWhite displays the response and stores bounded evidence locally.

Supported viewer ports in v0.2 are `80`, `443`, `8000`, `8080`, and `8443`.

### Bluetooth / BLE

1. Scan Bluetooth.
2. Enroll the BLE device.
3. Click **Inspect Access**.
4. AgentWhite establishes an ordinary BLE client session, maps GATT services and characteristics, and displays values the device permits the client to read.
5. A finding is recorded with remediation guidance for data that should have required stronger pairing, encryption, or application-layer authorization.

## Offline AI Analyst

If Ollama is installed locally and already has a model downloaded, open **AI Analyst** from the AgentWhite toolbar. The analyst uses AgentWhite findings as evidence rather than inventing attack results.

Set a preferred local model with:

```powershell
$env:AGENTWHITE_MODEL="llama3.2:3b"
```

If no local model is available, AgentWhite continues to operate with its built-in rules.

## Linux notes

AgentWhite uses `nmcli` for Wi-Fi discovery when available, `bluetoothctl` as a Bluetooth fallback, and `ip neigh` for LAN neighbors. Installing the Bluetooth extra enables the richer Bleak scanner and GATT inspector.

```bash
pip install -e ".[bluetooth]"
python3 -m agentwhite.server
```

## Scope model

Passive discovery can list devices and networks visible to the host. **Active validation, resource retrieval, and BLE post-access inspection are disabled until the target is explicitly enrolled in AgentWhite.** Enrollment state is stored locally and displayed in the UI.

## Evidence and data location

Windows database:

`%LOCALAPPDATA%\AgentWhite\agentwhite.db`

Windows evidence files:

`%LOCALAPPDATA%\AgentWhite\evidence\`

Linux/macOS:

`~/.agentwhite/agentwhite.db`

and:

`~/.agentwhite/evidence/`

## Current milestone

v0.2 adds the verified-access layer: AgentWhite can show what a reachable HTTP resource actually returns and what an enrolled BLE device actually exposes to a connected client, while preserving the local AI evidence-analysis workflow. The next milestone is richer protocol-specific validators, PCAP evidence capture, adapter capability detection, attack-path visualization, and locally generated assessment reports.
