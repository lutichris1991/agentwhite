# AgentWhite

AgentWhite is a local-first wireless and device security validation console for networks and hardware you own or are explicitly authorized to test.

The operating model is deliberately operator-controlled:

**discover -> enroll -> choose one test -> run it -> save result/access -> show next available choices -> wait for the operator**

AgentWhite does not automatically chain from one test into another.

## Operator modes

AgentWhite v0.7 introduces two operator experiences over the same underlying validation engine.

On first run, AgentWhite displays a mode-selection prompt that explains both choices before the user continues. The selected mode is stored locally in the browser and can later be changed from the Tool Center.

### Simple Button Mode

Simple Button Mode is the guided AgentWhite experience.

- actions are presented as clear buttons;
- only actions available for the current target/tool are shown;
- target workspaces, findings, evidence, and history remain visible;
- one selected action runs at a time;
- AgentWhite stops after each result and waits for the operator.

This mode is intended for fast, repeatable validation and for operators who do not need to enter action identifiers manually.

### Advanced Manual Mode

Advanced Manual Mode exposes a more direct expert interface while using the same AgentWhite backend and evidence model.

- operators can enter registered tool-action IDs directly;
- operators can select enrolled targets and enter available target-action IDs directly;
- the UI shows the exact request that will be submitted;
- raw JSON results are shown without hiding the underlying response data;
- action history, evidence, elapsed time, findings, and target workspaces are retained;
- automatic chaining remains disabled.

Advanced Manual Mode is intentionally more flexible than Simple Button Mode, but it is **not an unrestricted shell or arbitrary command runner**. AgentWhite still requires registered actions and explicit target enrollment where applicable, rejects unknown/out-of-scope actions, records execution history, and keeps one-action-per-submit behavior. Arbitrary external-tool command lines are not accepted through this interface.

Both modes are intended only for systems the operator owns or is explicitly authorized to assess.

## Tool Registry

The **Tool Registry** is the integration layer for third-party open-source security, radio, protocol, electronics, and hardware-analysis projects.

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

The registry is the foundation for adding curated external engines one adapter at a time. Registering a tool does not automatically enable all of its upstream commands.

Newly discovered capabilities become new buttons in Simple Mode and registered/available action choices in Advanced Mode; they are never executed automatically.

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

On first run, choose **Simple Button Mode** or **Advanced Manual Mode**. The choice is stored locally and can be changed later in **Tool Center**.

Use **Target Workspaces** for persistent engagements and **Tool Registry** to inspect the available integration stack.

## Run directly

Base application:

```bash
python app.py
```

or after installing the package:

```bash
agentwhite
```

For BLE discovery and inspection:

```bash
pip install -e ".[bluetooth]"
agentwhite
```

The installed `agentwhite` command routes through the UI launcher so the first-run mode chooser and current UI preparation are enabled.

## Offline AI Analyst

If Ollama is installed locally and already has a model downloaded, AgentWhite can analyze evidence without a cloud connection.

```powershell
$env:AGENTWHITE_MODEL="llama3.2:3b"
```

The workflow engine itself does not require an LLM. Test availability and next-step choices are deterministic software logic.

## Scope model

Passive discovery can list devices and networks visible to the host. Active validation, resource retrieval, BLE post-access inspection, and future third-party active adapters remain disabled until the target is explicitly enrolled.

Advanced Manual Mode does not change the scope model. It changes how the operator selects and inspects registered actions, not whether scope checks exist.

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

v0.7 adds first-run operator-mode selection plus a persistent Simple/Advanced Tool Center switch. Simple Mode preserves the current guided button workflow. Advanced Mode adds manual registered-action entry, enrolled-target selection, request previews, and raw JSON result inspection while preserving AgentWhite's scope, logging, and stop-after-result behavior.
