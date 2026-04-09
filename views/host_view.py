import streamlit as st
import time
from modules.host_tunnel import start_tunnel, stop_tunnel
from modules.host_files import render_file_viewer_tab
from modules.host_security import render_security_tab

def render_host():
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
                    render_file_viewer_tab()

                with tab3:
                    render_security_tab()
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
