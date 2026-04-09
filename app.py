import streamlit as st
import subprocess
import threading
import time
import re
import os

st.set_page_config(page_title="SFTP Hub", page_icon="🔒", layout="wide")

# ================= STATE INIT =================
if "app_mode" not in st.session_state:
    st.session_state.app_mode = "Landing"

# Host Mode State
if "process" not in st.session_state:
    st.session_state.process = None
if "logs" not in st.session_state:
    st.session_state.logs = []
if "host" not in st.session_state:
    st.session_state.host = None
if "port" not in st.session_state:
    st.session_state.port = None
if "username" not in st.session_state:
    st.session_state.username = None
if "password" not in st.session_state:
    st.session_state.password = None

# Client Mode State
if "client_sftp" not in st.session_state:
    st.session_state.client_sftp = None
if "client_ssh" not in st.session_state:
    st.session_state.client_ssh = None

# ================= HOST MODE =================
def start_tunnel(username, password):
    if st.session_state.process is not None:
        st.warning("Tunnel is already running.")
        return
    
    st.session_state.logs = []
    st.session_state.host = None
    st.session_state.port = None
    st.session_state.username = username
    st.session_state.password = password

    if os.name == 'nt':
        cmd = ["wsl", "-u", "root", "python3", "-u", "start_sftp.py", username, password]
    else:
        cmd = ["python3", "-u", "start_sftp.py", username, password]

    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        st.session_state.process = process
    except Exception as e:
        st.error(f"Failed to start process: {e}")
        return

    def reader_thread(proc):
        for line in iter(proc.stdout.readline, ''):
            if not line:
                break
            line_str = line.strip()
            if line_str:
                st.session_state.logs.append(line_str)
                
                if st.session_state.host is None and "tcp://" in line_str:
                    match = re.search(r"tcp://([a-zA-Z0-9\-.]+):(\d+)", line_str)
                    if match:
                        st.session_state.host = match.group(1)
                        st.session_state.port = match.group(2)
        proc.stdout.close()

    from streamlit.runtime.scriptrunner import add_script_run_ctx
    t = threading.Thread(target=reader_thread, args=(process,), daemon=True)
    add_script_run_ctx(t)
    t.start()
    
    time.sleep(3)

def stop_tunnel():
    if st.session_state.process is not None:
        st.session_state.process.terminate()
        st.session_state.process = None
        st.success("Tunnel stopped successfully.")

def host_mode():
    if st.button("← Back to Home"):
        st.session_state.app_mode = "Landing"
        st.rerun()

    st.title("🏠 SFTP Tunneler Host")
    st.markdown("Host a secure SFTP tunnel from your machine.")

    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            user_input = st.text_input("Username", value="admin")
        with col2:
            pass_input = st.text_input("Password", type="password")
        
        b_col1, b_col2 = st.columns([1, 1])
        with b_col1:
            if st.button("Start Tunnel", type="primary", use_container_width=True):
                if not user_input or not pass_input:
                    st.error("Please provide both Username and Password.")
                else:
                    with st.spinner("Starting Tunnel..."):
                        start_tunnel(user_input, pass_input)
                    st.rerun()
                    
        with b_col2:
            if st.button("Stop Tunnel", use_container_width=True):
                stop_tunnel()
                st.rerun()

    st.divider()

    if st.session_state.process is not None:
        if st.session_state.process.poll() is None:
            st.success("🟢 Tunnel is RUNNING")
            
            if st.session_state.host and st.session_state.port:
                tab1, tab2, tab3 = st.tabs(["Connection Details", "File Viewer", "Security & Access"])
                
                with tab1:
                    st.subheader("Connection Details")
                    st.markdown(f"**Host:** `{st.session_state.host}`")
                    st.markdown(f"**Port:** `{st.session_state.port}`")
                    st.markdown(f"**Username:** `{st.session_state.username}`")
                    st.markdown(f"**Password:** `{st.session_state.password}`")
                    
                    st.markdown("**Full SFTP Command:**")
                    sftp_cmd = f"sftp -P {st.session_state.port} {st.session_state.username}@{st.session_state.host}"
                    st.code(sftp_cmd, language="bash")
                    
                    st.divider()
                    st.subheader("How to Connect")
                    st.markdown(f"1. Open your local terminal/command prompt.\n"
                                f"2. Run the SFTP command above.\n"
                                f"3. When prompted, enter the password: `{st.session_state.password}`")
                    
                    st.subheader("File Location Info")
                    st.info(f"📁 **Remote Path:** Uploaded files will be stored in `/home/{st.session_state.username}/` on the server.")
                    st.info("⬇️ **Local Path:** Downloaded files will be saved to whichever folder you ran the `sftp` terminal command from.")
                    
                    st.subheader("Basic Commands")
                    st.markdown("- `ls` → List files on the remote server\n"
                                "- `put <filename>` → Upload a file to the server\n"
                                "- `get <filename>` → Download a file from the server\n"
                                "- `exit` → Close the SFTP session")

                with tab2:
                    st.subheader("Remote File Viewer")
                    st.markdown(f"Currently viewing: `/home/{st.session_state.username}/`")
                    
                    available_files = []
                    try:
                        if os.name == 'nt':
                            list_cmd = ["wsl", "-u", "root", "sh", "-c", f"ls -1p /home/{st.session_state.username} | grep -v / || true"]
                        else:
                            list_cmd = ["sh", "-c", f"ls -1p /home/{st.session_state.username} | grep -v / || true"]
                        
                        raw_files = subprocess.check_output(list_cmd, text=True).strip()
                        if raw_files:
                            available_files = [f for f in raw_files.split("\n") if f.strip() != ""]
                    except Exception:
                        pass

                    if st.button("Refresh Files"):
                        if os.name == 'nt':
                            ls_cmd = ["wsl", "-u", "root", "ls", "-la", f"/home/{st.session_state.username}"]
                        else:
                            ls_cmd = ["ls", "-la", f"/home/{st.session_state.username}"]
                        
                        try:
                            ls_out = subprocess.check_output(ls_cmd, text=True, stderr=subprocess.STDOUT)
                            st.code(ls_out, language="text")
                        except Exception as e:
                            st.error(f"Failed to list files or directory doesn't exist yet: {e}")
                    
                    st.divider()
                    st.subheader("File Operations")
                    
                    op_col1, op_col2 = st.columns(2)
                    
                    with op_col1:
                        st.markdown("**📤 Upload to Server**")
                        uploaded_file = st.file_uploader("Choose a file to push via tunnel:", label_visibility="collapsed")
                        if uploaded_file is not None:
                            if st.button("Confirm Upload", type="primary"):
                                with st.spinner("Uploading file safely..."):
                                    try:
                                        file_bytes = uploaded_file.getvalue()
                                        target_path = f"/home/{st.session_state.username}/{uploaded_file.name}"
                                        
                                        if os.name == 'nt':
                                            push_cmd = ["wsl", "-u", "root", "sh", "-c", f"cat > '{target_path}'"]
                                        else:
                                            push_cmd = ["sh", "-c", f"cat > '{target_path}'"]
                                        
                                        proc = subprocess.Popen(push_cmd, stdin=subprocess.PIPE, stderr=subprocess.STDOUT)
                                        proc.communicate(input=file_bytes)
                                        
                                        if os.name == 'nt':
                                            subprocess.run(["wsl", "-u", "root", "chown", f"{st.session_state.username}:{st.session_state.username}", target_path], check=False)
                                        else:
                                            subprocess.run(["sudo", "-n", "chown", "-R", f"{st.session_state.username}:{st.session_state.username}", target_path], check=False)

                                        st.success(f"{uploaded_file.name} uploaded successfully!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Upload failed: {e}")

                    with op_col2:
                        st.markdown("**📥 Download from Server**")
                        if not available_files:
                            st.info("The root of the directory has no files to download yet.")
                        else:
                            selected_file = st.selectbox("Select a file from the server:", available_files)
                            
                            try:
                                dl_path = f"/home/{st.session_state.username}/{selected_file}"
                                if os.name == 'nt':
                                    dl_cmd = ["wsl", "-u", "root", "cat", dl_path]
                                else:
                                    dl_cmd = ["cat", dl_path]
                                    
                                file_data = subprocess.check_output(dl_cmd)
                                st.download_button(
                                    label=f"Download '{selected_file}'",
                                    data=file_data,
                                    file_name=selected_file,
                                    use_container_width=True
                                )
                            except Exception as e:
                                st.error(f"Could not prepare download for {selected_file}.")

                with tab3:
                    st.subheader("Security & Network Access")
                    
                    wsl_pfx = ["wsl", "-u", "root"] if os.name == 'nt' else ["sudo", "-n"]
                    
                    # Fetch active IP rules dynamically
                    whitelisted = []
                    blacklisted = []
                    try:
                        raw_rules = subprocess.check_output(wsl_pfx + ["iptables", "-L", "INPUT", "-n"], text=True)
                        for line in raw_rules.split("\n"):
                            parts = line.split()
                            if len(parts) >= 4:
                                target = parts[0]
                                ip = parts[3]
                                if ip == "0.0.0.0/0" or ip == "Any": continue
                                if target == "ACCEPT":
                                    whitelisted.append(ip)
                                elif target == "DROP" and "dpt:2222" not in line:
                                    blacklisted.append(ip)
                    except Exception:
                        pass

                    # Global Mode
                    st.markdown("**🛡️ Global Firewall Mode**")
                    mode_col1, mode_col2 = st.columns([3, 1])
                    with mode_col1:
                        new_mode = st.radio("Select how the server handles incoming connections:", 
                            ["Default Mode (Reject only known threats)", "Whitelist Mode (Total Lockdown)"],
                            horizontal=True, label_visibility="collapsed")
                    with mode_col2:
                        if st.button("Apply Mode", type="primary", use_container_width=True):
                            with st.spinner("Modifying System Netfilter..."):
                                try:
                                    # Clear the master drop rule unconditionally to avoid duplicates
                                    subprocess.run(wsl_pfx + ["iptables", "-D", "INPUT", "-p", "tcp", "--dport", "2222", "-j", "DROP"], stderr=subprocess.DEVNULL)
                                    if "Whitelist" in new_mode:
                                        # Apply the master drop at the end of the chain securely
                                        subprocess.run(wsl_pfx + ["iptables", "-A", "INPUT", "-p", "tcp", "--dport", "2222", "-j", "DROP"], check=True)
                                        st.success("Strict Whitelist Mode applied!")
                                    else:
                                        st.success("Default Mode active! (Master drop removed)")
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to change mode: {e}")

                    st.divider()

                    w_col, b_col = st.columns(2)
                    
                    with w_col:
                        st.markdown("### 🟢 Whitelist")
                        st.caption("IPs inherently trusted by the system.")
                        wl_raw = st.text_input("Add to Whitelist:", key="wl_in", placeholder="e.g. 192.168.1.5", label_visibility="collapsed")
                        if st.button("Add to Whitelist", key="btn_wl", use_container_width=True):
                            if wl_raw:
                                try:
                                    subprocess.run(wsl_pfx + ["iptables", "-I", "INPUT", "1", "-s", wl_raw, "-j", "ACCEPT"], check=True)
                                    st.success(f"Added {wl_raw}.")
                                    time.sleep(0.5)
                                    st.rerun()
                                except Exception: st.error("Failed.")
                                
                        st.markdown("**Currently Whitelisted:**")
                        if not whitelisted: st.info("No IPs currently whitelisted.")
                        for idx, ip in enumerate(whitelisted):
                            c1, c2 = st.columns([3, 1])
                            c1.code(ip)
                            if c2.button("Remove", key=f"rm_w_{idx}_{ip}", type="secondary"):
                                subprocess.run(wsl_pfx + ["iptables", "-D", "INPUT", "-s", ip, "-j", "ACCEPT"])
                                st.rerun()

                    with b_col:
                        st.markdown("### 🔴 Blacklist")
                        st.caption("IPs permanently banished from tunneling.")
                        bl_raw = st.text_input("Add to Blacklist:", key="bl_in", placeholder="e.g. 10.0.0.5", label_visibility="collapsed")
                        if st.button("Add to Blacklist", key="btn_bl", use_container_width=True):
                            if bl_raw:
                                try:
                                    subprocess.run(wsl_pfx + ["iptables", "-I", "INPUT", "2", "-s", bl_raw, "-j", "DROP"], check=True)
                                    st.success(f"Banned {bl_raw}.")
                                    time.sleep(0.5)
                                    st.rerun()
                                except Exception: st.error("Failed.")
                                
                        st.markdown("**Currently Blacklisted:**")
                        if not blacklisted: st.info("No IPs currently blacklisted.")
                        for idx, ip in enumerate(blacklisted):
                            c1, c2 = st.columns([3, 1])
                            c1.code(ip)
                            if c2.button("Remove", key=f"rm_b_{idx}_{ip}", type="secondary"):
                                subprocess.run(wsl_pfx + ["iptables", "-D", "INPUT", "-s", ip, "-j", "DROP"])
                                st.rerun()
                                
                    st.divider()
                    st.markdown("**🔐 Authentication Ledger**")
                    st.caption("A clean audit log of who tried to access the tunnel.")
                    
                    auth_events = []
                    for log_line in st.session_state.logs:
                        if "[SUCCESS]" in log_line or "[FAILED]" in log_line or "[BLOCKING]" in log_line:
                            auth_events.append(log_line)
                    
                    if auth_events:
                        st.code("\n".join(auth_events), language="text")
                    else:
                        st.info("No authentication attempts logged yet.")
            else:
                st.warning("Waiting for connection details...")
                time.sleep(1)
                st.rerun()
        else:
            st.error("🔴 Tunnel process has died.")
            st.session_state.process = None

    else:
        st.info("⚪ Tunnel is STOPPED.")

    st.divider()
    st.subheader("Live Logs")
    if st.button("↻ Refresh Logs"):
        st.rerun()
        
    if st.session_state.logs:
        log_text = "\n".join(st.session_state.logs)
        st.text_area("Logs Stream", value=log_text, height=300, disabled=True)
    else:
        st.text("No logs available.")

# ================= CLIENT MODE =================
def client_mode():
    if st.button("← Back to Home"):
        st.session_state.app_mode = "Landing"
        # Close connection if leaving client page
        if st.session_state.client_sftp:
            try: st.session_state.client_sftp.close()
            except: pass
        if st.session_state.client_ssh:
            try: st.session_state.client_ssh.close()
            except: pass
        st.session_state.client_sftp = None
        st.session_state.client_ssh = None
        st.rerun()
    
    st.title("🌐 SFTP Client Connect")
    st.markdown("Connect securely to an external SFTP tunnel directly from your browser.")

    if st.session_state.client_sftp is None:
        with st.form("client_login_form"):
            st.subheader("Login Credentials")
            c1, c2 = st.columns(2)
            login_host = c1.text_input("Host (e.g. xpzih-xyz.run.pinggy-free.link)")
            login_port = c2.number_input("Port", min_value=1, max_value=65535, value=443)
            login_user = c1.text_input("Username")
            login_pass = c2.text_input("Password", type="password")
            
            submitted = st.form_submit_button("Connect Securely", type="primary", use_container_width=True)
            
            if submitted:
                if login_host and login_port and login_user and login_pass:
                    with st.spinner("Establishing SSH connection (this may take a few seconds)..."):
                        try:
                            import paramiko
                            ssh = paramiko.SSHClient()
                            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                            # 10 second timeout for graceful failure
                            ssh.connect(hostname=login_host, port=int(login_port), username=login_user, password=login_pass, timeout=10)
                            sftp = ssh.open_sftp()
                            
                            st.session_state.client_ssh = ssh
                            st.session_state.client_sftp = sftp
                            st.rerun()
                        except ImportError:
                            st.error("Critical Dependency Missing: Please run `pip install paramiko`")
                        except Exception as e:
                            st.error(f"Failed to connect. Check your credentials and ensure the host is online. Error: {e}")
                else:
                    st.error("Please fill in all connection fields.")
    else:
        st.success("🟢 Connected successfully!")
        if st.button("Disconnect", type="primary"):
            st.session_state.client_sftp.close()
            st.session_state.client_ssh.close()
            st.session_state.client_sftp = None
            st.session_state.client_ssh = None
            st.rerun()
            
        st.divider()
        sftp = st.session_state.client_sftp
        
        # Simple File Browser
        st.subheader("Remote File Browser")
        try:
            cwd = sftp.normalize(".")
            st.caption(f"Currently viewing root directory: `{cwd}`")
            # Minimal file listing (ignoring directories for MVP)
            # Paramiko listdir_attr returns SFTPAttributes which contain stat mode
            import stat
            remote_attrs = sftp.listdir_attr(cwd)
            files_only = [f.filename for f in remote_attrs if stat.S_ISREG(f.st_mode)]
            
            st.info(f"**{len(files_only)}** files available.")
            
        except Exception as e:
            st.error(f"Connection lost or directory error: {e}")
            files_only = []
            
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📤 Upload File**")
            uploaded_file = st.file_uploader("Upload to server", label_visibility="collapsed", key="cu")
            if uploaded_file:
                if st.button("Confirm Upload", type="secondary"):
                    with st.spinner("Uploading..."):
                        try:
                            # Paramiko putfo puts file-like objects directly
                            remote_path = cwd + "/" + uploaded_file.name
                            sftp.putfo(uploaded_file, remote_path)
                            st.success("Uploaded securely!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Upload failed: {e}")
                            
        with col2:
            st.markdown("**📥 Download File**")
            if not files_only:
                st.info("Directory is empty.")
            else:
                sel_file = st.selectbox("Select file to download", files_only)
                if st.button("Prepare Download"):
                    with st.spinner("Fetching data from tunnel..."):
                        try:
                            remote_path = cwd + "/" + sel_file
                            import io
                            flo = io.BytesIO()
                            sftp.getfo(remote_path, flo)
                            flo.seek(0)
                            
                            st.download_button(
                                label=f"Confirm Download: {sel_file}",
                                data=flo,
                                file_name=sel_file,
                                use_container_width=True
                            )
                        except IOError as e:
                            st.error(f"Cannot download file. It may be locked or inaccessible: {e}")

# ================= ROUTING =================
def main():
    if st.session_state.app_mode == "Landing":
        st.title("Welcome to SFTP Hub 🚀")
        st.markdown("Your all-in-one suite for crafting secure tunnels and managing remote files.")
        st.divider()
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 🏠 Host Server")
            st.info("Start a local SFTP tunnel, generate secure endpoints, and manage active IP firewall rules.")
            if st.button("Start Hosting", use_container_width=True, type="primary"):
                st.session_state.app_mode = "Host"
                st.rerun()
                
        with c2:
            st.markdown("### 🌐 Connect Client")
            st.info("Log into a friend's active tunnel remotely. Use the sleek GUI to upload and download files.")
            if st.button("Connect to Server", use_container_width=True, type="primary"):
                st.session_state.app_mode = "Client"
                st.rerun()
                
    elif st.session_state.app_mode == "Host":
        host_mode()
        
    elif st.session_state.app_mode == "Client":
        client_mode()

if __name__ == "__main__":
    main()
