# AgentWhite

AgentWhite is a local-first wireless and device security validation console for networks and hardware you own or are explicitly authorized to test.

The operating model is deliberately operator-controlled:

**discover -> enroll -> choose one test -> run it -> save result/access -> show next available choices -> wait for the operator**

AgentWhite does not automatically chain from one test into another.

## What v0.3 adds

v0.3 introduces persistent **Target Workspaces**. Enrollment creates or resumes an engagement for that specific target. The workspace keeps prior work available while you move between newly discovered options.

Each workspace contains:

- **Overview** — engagement status and counts.
- **Tests** — only the actions currently available for that target. Clicking one runs only that selected test.
- **Saved Access** — verified or reachable access points discovered during earlier tests.
- **History** — every explicitly run action, start/completion time, elapsed milliseconds, result, and status.
- **Findings** — proof plus remediation guidance.

Pausing/removing a target from active scope does not erase its workspace. Re-enrolling resumes the saved engagement. A workspace can also be explicitly cleared from the UI.

## Current test modules

The v0.3 workflow engine exposes the capabilities already implemented by AgentWhite rather than inventing results:

- Wi-Fi configuration audit for an enrolled access point.
- Conservative TCP service verification for an enrolled private/local LAN device.
- HTTP/HTTPS returned-material viewer for verified local web services.
- Read-only BLE GATT service/characteristic inspection for an enrolled Bluetooth target.

Newly discovered capabilities become new buttons in the workspace; they are never executed automatically.

## Proof and access history

Successful/reachable access points are saved separately from test history. This lets you return to an earlier target path without discarding later discoveries.

For example, after LAN service verification finds a reachable local HTTP service, AgentWhite records the test and adds a saved HTTP access card. Opening that card later does not remove the original service-verification record.

BLE inspection records a logical reconnectable access point because the ordinary BLE client operation used by the current inspector is not represented as a permanently open socket. The evidence and route remain saved even if the transport itself must reconnect.

## Existing v0.2 capabilities retained

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

### Install from the repository

Requirements: Windows 10/11 and Python 3.11+.

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install_windows.ps1
```

AgentWhite opens locally at:

`http://127.0.0.1:8765`

Use **Target Workspaces** in the main toolbar to enter the persistent engagement view.

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

Passive discovery can list devices and networks visible to the host. Active validation, resource retrieval, and BLE post-access inspection remain disabled until the target is explicitly enrolled.

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

v0.3 establishes the persistent engagement model: tests, access points, findings, timing, evidence, and available next actions stay attached to the target while AgentWhite waits for explicit operator input before every next test.
