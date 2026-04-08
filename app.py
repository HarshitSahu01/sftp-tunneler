import streamlit as st
import subprocess
import threading
import time
import re

st.set_page_config(page_title="SFTP Tunneler", page_icon="🔒")

# Initialize session state
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

def start_tunnel(username, password):
    if st.session_state.process is not None:
        st.warning("Tunnel is already running.")
        return
    
    st.session_state.logs = []
    st.session_state.host = None
    st.session_state.port = None
    st.session_state.username = username
    st.session_state.password = password

    import os
    if os.name == 'nt':
        # On Windows, we use WSL as root to execute the Linux script
        cmd = ["wsl", "-u", "root", "python3", "-u", "start_sftp.py", username, password]
    else:
        cmd = ["python3", "-u", "start_sftp.py", username, password]

    # We use subprocess.PIPE to read stdout. stderr is redirected to stdout.
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
                
                # Check for successfully parsed host and port from pinggy output
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
    
    # Wait briefly to catch the Host/Port
    time.sleep(3)

def stop_tunnel():
    if st.session_state.process is not None:
        # Terminate the process cleanly
        st.session_state.process.terminate()
        st.session_state.process = None
        st.success("Tunnel stopped successfully.")

st.title("SFTP Tunneler")
st.markdown("A lightweight web-based control panel for your secure SFTP tunnel.")

# Form & Button Inputs
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
    # We check if process is still running
    if st.session_state.process.poll() is None:
        st.success("🟢 Tunnel is RUNNING")
        
        if st.session_state.host and st.session_state.port:
            tab1, tab2 = st.tabs(["Connection Details", "File Viewer"])
            
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
                import os
                
                # Fetch available files for the download dropdown
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
                                    
                                    # Chown so the connected user has correct ownership rights to their own file
                                    if os.name == 'nt':
                                        subprocess.run(["wsl", "-u", "root", "chown", f"{st.session_state.username}:{st.session_state.username}", target_path], check=False)
                                    
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
    
# Display logs inside a scrollable fixed-height textbox
if st.session_state.logs:
    log_text = "\n".join(st.session_state.logs)
    st.text_area("Logs Stream", value=log_text, height=300, disabled=True)
else:
    st.text("No logs available.")
