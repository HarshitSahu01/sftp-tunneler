import streamlit as st
import time

def connect_ssh(login_host, login_port, login_user, login_pass):
    try:
        import paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=login_host, port=int(login_port), username=login_user, password=login_pass, timeout=10)
        sftp = ssh.open_sftp()
        
        st.session_state.client_ssh = ssh
        st.session_state.client_sftp = sftp
        st.rerun()
    except ImportError:
        st.error("Critical Dependency Missing: Please run `pip install paramiko`")
    except Exception as e:
        st.error(f"Failed to connect. Check your credentials and ensure the host is online. Error: {e}")

def render_file_browser(sftp):
    st.subheader("Remote File Browser")
    try:
        cwd = sftp.normalize(".")
        st.caption(f"Currently viewing root directory: `{cwd}`")
        import stat
        remote_attrs = sftp.listdir_attr(cwd)
        files_only = [f.filename for f in remote_attrs if stat.S_ISREG(f.st_mode)]
        st.info(f"**{len(files_only)}** files available.")
    except Exception as e:
        st.error(f"Connection lost or directory error: {e}")
        files_only = []
        cwd = "."
        
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📤 Upload File**")
        uploaded_file = st.file_uploader("Upload to server", label_visibility="collapsed", key="cu")
        if uploaded_file:
            if st.button("Confirm Upload", type="secondary"):
                with st.spinner("Uploading..."):
                    try:
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
