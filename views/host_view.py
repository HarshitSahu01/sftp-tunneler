import streamlit as st
import time
import json
from urllib.parse import urlencode
import streamlit.components.v1 as components
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
                    
                    private_host = st.session_state.private_host
                    private_port = st.session_state.private_port or "22"
                    if private_host:
                        private_cmd = f"sftp -P {private_port} {st.session_state.username}@{private_host}"
                        st.markdown("**Private SFTP Command (Local Network):**")
                        st.code(private_cmd, language="bash")

                    st.markdown("**Public SFTP Command (Pinggy):**")
                    sftp_cmd = f"sftp -P {st.session_state.port} {st.session_state.username}@{st.session_state.host}"
                    st.code(sftp_cmd, language="bash")

                    st.divider()
                    st.subheader("SFTP Web Client")
                    filestash_url = "https://demo.filestash.app/login?" + urlencode(
                        {
                            "type": "sftp",
                            "hostname": st.session_state.host,
                            "username": st.session_state.username,
                            "password": st.session_state.password,
                            "port": st.session_state.port,
                        }
                    )

                    st.link_button("Open SFTP Web Client", filestash_url, use_container_width=True)

                    copy_btn_id = f"copy-filestash-{st.session_state.port}"
                    copy_label_id = f"copy-label-{st.session_state.port}"
                    copy_widget = f"""
                    <div style="display:flex;align-items:center;gap:8px;margin-top:8px;">
                        <button id="{copy_btn_id}" style="padding:8px 12px;border-radius:8px;border:1px solid #d1d5db;background:#ffffff;cursor:pointer;">📋 Copy Link</button>
                        <span id="{copy_label_id}" style="font-size:0.9rem;color:#4b5563;"></span>
                    </div>
                    <script>
                        const copyBtn = document.getElementById({json.dumps(copy_btn_id)});
                        const copyLabel = document.getElementById({json.dumps(copy_label_id)});
                        if (copyBtn) {{
                            copyBtn.onclick = async () => {{
                                try {{
                                    await navigator.clipboard.writeText({json.dumps(filestash_url)});
                                    if (copyLabel) copyLabel.textContent = "Copied";
                                }} catch (err) {{
                                    if (copyLabel) copyLabel.textContent = "Copy failed";
                                }}
                            }};
                        }}
                    </script>
                    """
                    components.html(copy_widget, height=52)
                    
                    st.divider()
                    st.subheader("How to Connect")
                    st.markdown(f"1. Open your local terminal/command prompt.\n"
                                f"2. Use the private command on your local network, or the public command from anywhere.\n"
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
