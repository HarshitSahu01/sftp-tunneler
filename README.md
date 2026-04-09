# SFTP Tunneler

A Streamlit-based SFTP toolkit for both hosting and connecting to tunneled SFTP servers.

The project currently uses **Pinggy** for reverse SSH tunneling and includes:
- A **Host mode** to create and expose a local SFTP server.
- A **Client mode** to connect to a remote SFTP tunnel from the browser.
- Built-in security tooling (whitelist/blacklist/global mode/auth log monitoring).

---

## Features

- **Dual App Modes**: Landing page routes into Host or Client workflows.
- **Host Tunnel Automation**: Installs/configures `openssh-server`, creates user credentials, and starts the Pinggy tunnel.
- **Live Connection Details**: Shows host, port, username, password, and generated `sftp -P <port> <user>@<host>` command.
- **Host File Operations**: Upload/download files directly against `/home/<username>/`.
- **Client File Browser**: Connect to a remote SFTP endpoint via Paramiko, then upload/download from a browser session.
- **Firewall Controls**: Default vs strict whitelist mode for port `2222`, plus IP whitelist/blacklist management.
- **Auth Event Ledger**: Displays successful, failed, and blocked authentication events from live tunnel logs.
- **Auto Blocking**: Repeated failed auth attempts are auto-blocked via `iptables` (after 3 failed attempts).
- **Cloud-Aware UI Behavior**: Host mode can be disabled in cloud deploys via `CLOUD_DEPLOYMENT` secret.

---

## Quick Start

### Prerequisites
- **OS**: Linux (Debian/Ubuntu recommended for host mode)
- **Python**: 3.8+
- **Privileges for Host Mode**: Root/sudo is required for `sshd`, `systemctl`, and `iptables` operations.

### Installation
1. **Clone the repository**:
   ```bash
   git clone https://github.com/HarshitSahu01/sftp-tunneler
   cd sftp-tunneler
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Run the Streamlit App (Recommended)
```bash
sudo streamlit run app.py
```

Why `sudo`: the Host workflow invokes system-level operations (`openssh-server`, `systemctl`, `iptables`) through `start_sftp.py`.

### Run Script-Only Mode (No UI)
If you only want the tunnel bootstrap script:

```bash
sudo python3 start_sftp.py <username> <password>
```

The script prints a public endpoint and SFTP command:

```bash
sftp -P <port> <username>@<host>
```

---

## How It Works

### Host Mode
- Accepts username/password and launches `start_sftp.py`.
- Parses live process logs to extract tunnel host/port.
- Exposes three tabs:
  - `Connection Details`
  - `File Viewer`
  - `Security & Access`

### Client Mode
- Uses Paramiko over SSH to open an SFTP session to a remote endpoint.
- Supports browser-side upload/download for files in the active remote directory.

### Security Layer
- Reads and manages `iptables` INPUT rules.
- Supports whitelist and blacklist CRUD from the UI.
- Can enforce a strict whitelist model by appending a terminal drop rule on SFTP port `2222`.
- Monitors `/var/log/auth.log` and blocks IPs after repeated failed attempts.

---

## Configuration

- `CLOUD_DEPLOYMENT` (Streamlit secret): when set truthy, disables Host mode buttons in the landing page.

---

## Dependencies

- `streamlit`
- `paramiko`

---

## Project Structure

```text
app.py                  # Streamlit entrypoint and routing
start_sftp.py           # System bootstrap + Pinggy tunnel + auth monitoring
views/host_view.py      # Host mode UI
views/client_view.py    # Client mode UI
modules/host_tunnel.py  # Host process lifecycle and log streaming
modules/host_files.py   # Host file viewer/upload/download
modules/host_security.py# Firewall and auth event UI
modules/client_core.py  # Paramiko SSH/SFTP client workflow
```

---

## Notes and Limitations

- Host mode is intended for local/native execution with elevated permissions.
- The tunnel backend is currently Pinggy.
- Firewall and auth monitoring behavior depends on Linux tooling (`iptables`, `/var/log/auth.log`).

---

## Roadmap

Long-term direction remains a custom forwarding and relay stack to reduce third-party tunnel dependency and add richer orchestration.

---

## Contributing

Contributions are welcome. Open an issue or submit a PR with bug fixes, improvements, or roadmap proposals.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
