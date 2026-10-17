# AgentWhite

**AgentWhite** is an offline-first security auditing workstation for wireless and local networks you own or are explicitly authorized to test.

Version `0.1.0` establishes the local architecture, discovery layer, target authorization boundary, proof/evidence workflow, offline analysis, and Windows packaging.

## What v0.1 does

- Runs locally on Windows and opens a browser-based command center at `http://127.0.0.1:8765`.
- Surveys nearby Wi-Fi networks using Windows `netsh`.
- Discovers devices already visible on the local LAN.
- Scans for Bluetooth Low Energy advertisements using `bleak`.
- Requires a target to be explicitly enrolled before active service checks.
- Checks a focused set of common TCP services on enrolled targets.
- Records validated observations in a local SQLite database.
- Lets you verify an HTTP/HTTPS resource on an enrolled device and view the returned text directly.
- Saves returned image evidence locally when an authorized HTTP endpoint exposes an image.
- Produces plain-English remediation guidance for validated findings.
- Uses a local Ollama model for AI analysis when one is installed; otherwise the built-in offline analyst works without an AI server.
- Keeps application data under `%USERPROFILE%\.agentwhite`.

## Agent model

The UI is one application, but the architecture follows a multi-agent workflow:

1. **Recon Agent** — Wi-Fi, LAN and BLE discovery.
2. **Scope Agent** — keeps discovery separate from explicitly authorized active targets.
3. **Service Agent** — validates reachable services on enrolled devices.
4. **Verification Agent** — asks “can I actually observe the claimed access?” and records evidence.
5. **Evidence Agent** — stores findings and proof locally.
6. **Remediation Agent** — turns each observation into patch guidance.
7. **Retest Agent** — rerun the same verification after a fix.
8. **AI Analyst** — optional local Ollama reasoning over evidence; never required for the app to work.

## Windows: fastest path

### Option A — download the built EXE

The included GitHub Actions workflow builds a standalone Windows executable. Open the repository's **Actions** tab, select **Build Windows EXE**, then download the `AgentWhite-Windows` artifact.

Extract it and run:

```text
AgentWhite.exe
```

The program starts a local server and opens the command center in your default browser. The executable does not require internet access at runtime.

### Option B — run from source

Install Python 3.11+ and run:

```bat
run_dev.bat
```

The first source installation needs Python packages from `requirements.txt`. Once installed, the application itself operates locally.

### Option C — build the EXE yourself

```bat
build_windows.bat
```

The executable will be created in `dist\AgentWhite.exe`.

## Optional offline AI

AgentWhite works without a language model. To add local AI analysis, install Ollama separately, download a model while you have internet access, and then run that model locally. AgentWhite detects the Ollama service at `127.0.0.1:11434` and lists installed models in the UI.

No cloud API key is required.

## Current verification boundary

v0.1 intentionally starts with **observable, reproducible checks** rather than reporting speculative exploits:

- TCP connection proof
- service/banner evidence where appropriate
- HTTP/HTTPS response proof
- returned text preview
- returned image evidence saved locally
- remediation generated from what was actually observed

The evidence system and UI are designed so additional authorized test modules can later return the same standardized result: **attempt → verified access → viewable evidence → remediation → retest**.

## Important

Only enroll systems you own or have explicit authorization to test. Wi-Fi/BLE discovery can observe devices that are not yours; discovery alone does **not** authorize active testing.

## Project status

Early prototype / `0.1.0`. Expect rapid iteration.
