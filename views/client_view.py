import streamlit as st
from modules.client_core import connect_ssh, render_file_browser

def render_client():
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
                        connect_ssh(login_host, login_port, login_user, login_pass)
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
        render_file_browser(st.session_state.client_sftp)
