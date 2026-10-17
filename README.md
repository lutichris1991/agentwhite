# AgentWhite

AgentWhite is a local-first wireless and device security validation console for networks and hardware you own or are explicitly authorized to test.

The operating model is deliberately operator-controlled:

**discover -> enroll -> choose one test -> run it -> save result/access -> show next available choices -> wait for the operator**

AgentWhite does not automatically chain from one test into another.

## What v0.4 adds

v0.4 introduces the **Tool Registry**, the integration layer for third-party open-source security, radio, protocol, electronics, and hardware-analysis projects.

The registry starts with a curated multi-protocol tool pack covering:

- Wi-Fi and 802.11 discovery/validation
- Bluetooth and BLE
- RFID and NFC
- SDR / general RF and ISM-band devices
- Zigbee / IEEE 802.15.4
- LAN and packet/protocol analysis
- Logic analyzers and general electronics capture
- JTAG / SWD embedded debug interfaces
- Firmware flash devices
- CAN bus / automotive / industrial interfaces
- UART / serial
- USB

The initial registry includes projects such as Kismet, Aircrack-ng, hcxtools, Bettercap, BlueZ, Bleak, Ubertooth, WHAD, Proxmark3, libnfc, HackRF, rtl_433, GNU Radio 4, KillerBee, TShark/Wireshark, Scapy, Nmap, sigrok-cli, OpenOCD, flashrom, python-can, can-utils, pySerial, and PyUSB.

### AgentWhite policy always stays above the external tool

Third-party tools do not get to control the workflow. Every registered integration inherits these AgentWhite rules:

- target enrollment is required before active validation;
- `auto_chain` is always false by default;
- every new test must be started by the operator;
- results remain attached to the persistent target workspace;
- elapsed time and result metadata are recorded;
- proof/evidence is preserved locally when the adapter supports it;
- remediation guidance stays attached to the resulting finding;
- disruptive capabilities require a separate policy gate before they are exposed.

The **Tool Registry** page shows which registered engines are detected on the local machine, their protocol/hardware family, integration method, effect level, hardware expectations, and packaging/license note.

## Third-party licensing and packaging

AgentWhite uses an adapter-first design instead of copying every upstream project's source code into this repository.

Some open-source projects impose redistribution, copyleft, attribution, source-availability, or commercial-integration obligations. Some projects use custom licenses. For that reason each registry entry carries a `bundle_policy` such as `external-only`, `system-component`, `separate-component`, or `candidate-bundled-dependency`.

A tool marked `external-only` should be installed separately by the user and controlled through an AgentWhite adapter rather than redistributed inside an AgentWhite binary. License metadata in the registry is a packaging hint, not legal advice; upstream license text remains authoritative and should be rechecked before a release bundles any third-party binary or source.

## Persistent Target Workspaces

Enrollment creates or resumes an engagement for that specific target. The workspace keeps prior work available while you move between newly discovered options.

Each workspace contains:

- **Overview** — engagement status and counts.
- **Tests** — only the actions currently available for that target. Clicking one runs only that selected test.
- **Saved Access** — verified or reachable access points discovered during earlier tests.
- **History** — every explicitly run action, start/completion time, elapsed milliseconds, result, and status.
- **Findings** — proof plus remediation guidance.

Pausing/removing a target from active scope does not erase its workspace. Re-enrolling resumes the saved engagement. A workspace can also be explicitly cleared from the UI.

## Current executable test modules

The workflow engine currently exposes the capabilities already implemented by AgentWhite rather than inventing results:

- Wi-Fi configuration audit for an enrolled access point.
- Conservative TCP service verification for an enrolled private/local LAN device.
- HTTP/HTTPS returned-material viewer for verified local web services.
- Read-only BLE GATT service/characteristic inspection for an enrolled Bluetooth target.

The v0.4 registry is the foundation for adding the curated external engines one adapter at a time. Registering a tool does not automatically enable all of its upstream commands.

Newly discovered capabilities become new buttons in the workspace; they are never executed automatically.

## Proof and access history

Successful/reachable access points are saved separately from test history. This lets you return to an earlier target path without discarding later discoveries.

For example, after LAN service verification finds a reachable local HTTP service, AgentWhite records the test and adds a saved HTTP access card. Opening that card later does not remove the original service-verification record.

BLE inspection records a logical reconnectable access point because the ordinary BLE client operation used by the current inspector is not represented as a permanently open socket. The evidence and route remain saved even if the transport itself must reconnect.

## Existing capabilities retained

- Runs on `127.0.0.1` with no cloud requirement.
- Discovers Wi-Fi, LAN neighbors, and Bluetooth/BLE devices using local OS/hardware interfaces.
- Requires explicit enrollment before active validation.
- Stores findings and workspace data locally in SQLite.
- Saves bounded HTTP evidence and SHA-256 hashes.
- Provides remediation guidance for recorded findings.
- Includes an optional local Ollama evidence analyst and a deterministic offline fallback.

## Windows installation

### Standalone Windows build

The repository includes `.github/workflows/build-windows.yml`. It builds `AgentWhite.exe` and uploads `AgentWhite-Windows.zip` as a GitHub Actions artifact.

External hardware tools may still require their own drivers, USB libraries, radio firmware, or separately installed command-line utilities. The Tool Registry reports what AgentWhite can currently detect.

### Install from the repository

Requirements: Windows 10/11 and Python 3.11+.

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install_windows.ps1
```

AgentWhite opens locally at:

`http://127.0.0.1:8765`

Use **Target Workspaces** for persistent engagements and **Tool Registry** to inspect the available integration stack.

## Run directly

Base application:

```bash
python -m agentwhite.server
```

For BLE discovery and inspection:

```bash
pip install -e ".[bluetooth]"
python -m agentwhite.server
```

## Offline AI Analyst

If Ollama is installed locally and already has a model downloaded, AgentWhite can analyze evidence without a cloud connection.

```powershell
$env:AGENTWHITE_MODEL="llama3.2:3b"
```

The workflow engine itself does not require an LLM. Test availability and next-step buttons are deterministic software logic.

## Scope model

Passive discovery can list devices and networks visible to the host. Active validation, resource retrieval, BLE post-access inspection, and future third-party active adapters remain disabled until the target is explicitly enrolled.

## Data location

Windows database:

`%LOCALAPPDATA%\AgentWhite\agentwhite.db`

Windows evidence:

`%LOCALAPPDATA%\AgentWhite\evidence\`

Linux/macOS:

`~/.agentwhite/agentwhite.db`

and:

`~/.agentwhite/evidence/`

## Current milestone

v0.4 establishes the curated third-party Tool Registry while preserving the v0.3 persistent engagement model. The next development step is implementing individual typed adapters so each supported external engine contributes only explicit AgentWhite-approved actions and normalized evidence/results to the same workspace UI.
