# 🚀 SFTP Tunneler

A lightweight, automated SSH/SFTP server and tunneling utility designed to expose local directories to the web with zero-config overhead.

Currently powered by **Pinggy**, this tool simplifies the deployment of an SFTP server on Linux environments, handling user management, service configuration, and secure tunneling in a single automated flow.

---

## 🛠️ Features

- **One-Command Setup**: Installs and configures `sshd` automatically.
- **Dynamic User Management**: Creates temporary or persistent SFTP users with custom credentials.
- **Secure Tunneling**: Zero-config reverse SSH tunneling via Pinggy (`tcp://...`).
- **Interactive Console**: Real-time display of connection details and SFTP access commands.
- **Clean Exit**: Automatically cleans up SSH services and tunnels on termination.

---

## 🚦 Quick Start

### Prerequisites
- **OS**: Linux (Debian/Ubuntu recommended)
- **Permissions**: Root access (`sudo`)
- **Python**: 3.8+

### Installation & Usage
1. **Clone the repository**:
   ```bash
   git clone https://github.com/HarshitSahu01/sftp-tunneler
   cd sftp-tunneler
   ```

2. **Run the tunneler**:
   ```bash
   sudo python3 start_sftp.py <username> <password>
   ```

3. **Profit**:
   The script will output the public URL and the command to connect from any remote machine:
   ```bash
   sftp -P <port> <username>@<host>
   ```

---

## 🚀 The Vision: Moving Beyond Pinggy

We are planning to evolve this tool into a full-featured, self-hosted **SFTP Relay Infrastructure**. This new architecture will eliminate dependencies on third-party tunnels and provide unparalleled control over your traffic.

### 🛡️ Custom Forwarding Utility (Future Roadmap)
Our goal is to build a bespoke tunneling proxy that offers:

- **Integrated Firewall**: Granular control over who can access your SFTP server based on IP or geolocation.
- **Real-time Monitoring**: Visual dashboards to track active connections, bandwidth usage, and transfer logs.
- **IP Management**: Dynamic whitelisting and blacklisting of remote clients.
- **Centralized Orchestration**: A Render-based control plane to manage multiple tunnels from a single interface.

---

## 🤝 Contributing

Contributions are welcome! Whether it's bug fixes, feature requests, or suggestions for the new architecture, please open an issue or submit a PR.

---

## 📜 License

MIT License. See [LICENSE](LICENSE) for details.
