import streamlit as st

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

from views.host_view import render_host
from views.client_view import render_client

# ================= ROUTING =================
def main():
    if st.session_state.app_mode == "Landing":
        st.title("Welcome to SFTP Hub 🚀")
        st.markdown("Your all-in-one suite for crafting secure tunnels and managing remote files.")
        st.divider()
        
        c1, c2 = st.columns(2)
        with c1:
            # Check for cloud deployment to hide Host mode if deployed on web
            # As discussed with Harshit, host mode is for local native use only
            try:
                is_cloud = st.secrets.get("CLOUD_DEPLOYMENT", False)
            except Exception:
                is_cloud = False
                
            if is_cloud:
                st.markdown("### 🏠 Host Server (Disabled)")
                st.info("Host Mode is disabled in the Cloud version. Please run this app locally to host files.")
                st.button("Start Hosting", use_container_width=True, type="primary", disabled=True)
            else:
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
        render_host()
        
    elif st.session_state.app_mode == "Client":
        render_client()

if __name__ == "__main__":
    main()
