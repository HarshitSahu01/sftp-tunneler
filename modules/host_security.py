import streamlit as st
import subprocess
import os
import time

def render_security_tab():
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
