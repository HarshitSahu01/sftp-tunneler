import streamlit as st
import subprocess
import os

def render_file_viewer_tab():
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
