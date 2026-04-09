import streamlit as st
import subprocess
import threading
import time
import re
import os

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
