import streamlit as st
import requests
import json
from datetime import datetime, timezone
from pathlib import Path

API_BASE = "http://localhost:8000/api/jupyter"
PORT_HISTORY_FILE = Path(__file__).parent / "port_history.json"

st.set_page_config(page_title="Jupyter Manager", layout="wide")
st.title("🧪 JupyterLab Instance Manager")

# ------------------------
# PORT HISTORY MANAGEMENT
# ------------------------
def load_port_history():
    """Load port history from JSON file"""
    if PORT_HISTORY_FILE.exists():
        try:
            with open(PORT_HISTORY_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_port_history(history):
    """Save port history to JSON file"""
    with open(PORT_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def update_port_history(port, tag):
    """Update port history with new usage
    Args:
        port: Port number
        tag: Tag string. If empty string, sets to "Untagged". If provided, updates tag.
    """
    history = load_port_history()
    port_str = str(port)
    
    if port_str not in history:
        history[port_str] = {
            "tag": tag if tag else "Untagged",
            "last_used": datetime.now(timezone.utc).isoformat(),
            "times_used": 1
        }
    else:
        # Always update tag (empty string will set to "Untagged")
        history[port_str]["tag"] = tag if tag else "Untagged"
        history[port_str]["last_used"] = datetime.now(timezone.utc).isoformat()
        history[port_str]["times_used"] = history[port_str].get("times_used", 0) + 1
    
    save_port_history(history)

def get_instances():
    """Get active Jupyter instances from API"""
    try:
        resp = requests.get(API_BASE)
        if resp.status_code != 200:
            return []
        return resp.json()
    except:
        return []

# ------------------------
# START NEW SESSION
# ------------------------
with st.expander("➕ Start New Jupyter Session", expanded=True):
    disable_timer = st.checkbox("Disable expiration timer", value=False, help="If enabled, the session will never expire automatically")
    
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

    if disable_timer:
        ttl = None
        col1.info("⏰ Timer disabled - session will not expire")
    else:
        ttl = col1.slider("Session duration (minutes)", 15, 1440, 60)

    # Optional port input using text_input
    user_port_raw = col2.text_input(
        "Port (optional, 9000–9100)",
        placeholder="Leave empty for auto-selection"
    )
    user_port = None
    if user_port_raw.strip():
        try:
            user_port = int(user_port_raw)
            if not (9000 <= user_port <= 9100):
                st.error("Port must be between 9000 and 9100")
                user_port = None
        except ValueError:
            st.error("Invalid port number")
            user_port = None
    
    tag_input = col3.text_input(
        "Tag (optional)",
        placeholder="e.g., My Project, Data Analysis"
    )

    password_input = col4.text_input(
        "Set password (optional)", type="password", placeholder="Auto-generated if empty"
    )

    if st.button("🚀 Start JupyterLab", type="primary"):
        params = {}
        if ttl is not None:
            params["session_minutes"] = ttl
        else:
            params["disable_timer"] = True
        if user_port:
            params["user_port"] = int(user_port)
        if password_input:
            params["password"] = password_input
        
        resp = requests.post(API_BASE, params=params)
        if resp.status_code == 200:
            data = resp.json()
            actual_port = data.get('port', user_port)
            
            # Save port history with tag
            if actual_port:
                update_port_history(actual_port, tag_input.strip() if tag_input else "")
            
            st.success("JupyterLab started successfully!")
            st.markdown("### 🔐 Access Details")
            st.markdown(f"- **URL:** [{data['url']}]({data['url']})")
            st.markdown(f"- **Password:** `{data['password']}`")
            st.markdown(f"- **Port:** {actual_port}")
            if tag_input.strip():
                st.markdown(f"- **Tag:** {tag_input}")
            if data.get('expires_at'):
                st.info(f"Expires at: {data['expires_at']} UTC")
            else:
                st.info("⏰ Timer disabled - session will not expire automatically")
            
            st.rerun()
        else:
            st.error(resp.json().get("detail", "Failed to start JupyterLab"))

# ------------------------
# OPEN PREVIOUSLY OPENED SESSIONS
# ------------------------
port_history = load_port_history()
if port_history:
    with st.expander("📂 Open Previously Opened Session", expanded=False):
        instances = get_instances()
        active_ports = {str(inst['port']) for inst in instances} if instances else set()
        
        # Create dropdown options with status
        port_options = []
        port_data_map = {}
        
        # Sort by last used (most recent first)
        for port, data in sorted(port_history.items(), key=lambda x: x[1].get("last_used", ""), reverse=True):
            tag = data.get("tag", "Untagged")
            is_active = str(port) in active_ports
            status = "🟢 Currently Active" if is_active else "⚪ Inactive"
            last_used = data.get("last_used", "")
            
            # Format last used date
            try:
                if last_used:
                    last_used_dt = datetime.fromisoformat(last_used.replace('Z', '+00:00'))
                    last_used_str = last_used_dt.strftime('%Y-%m-%d %H:%M')
                else:
                    last_used_str = "Unknown"
            except:
                last_used_str = last_used[:10] if last_used else "Unknown"
            
            display_text = f"Port {port} - {tag} ({status}) | Last used: {last_used_str}"
            port_options.append(display_text)
            port_data_map[display_text] = {
                "port": int(port),
                "tag": tag,
                "is_active": is_active,
                "data": data
            }
        
        if port_options:
            selected_session = st.selectbox(
                "Select a previously opened session",
                options=port_options,
                key="previous_session_select",
                help="Select a port from your history to open a new session with the same port and tag"
            )
            
            if selected_session:
                session_info = port_data_map[selected_session]
                selected_port = session_info["port"]
                selected_tag = session_info["tag"]
                is_active = session_info["is_active"]
                
                # Use selected_port in keys to force update when dropdown changes
                port_key = f"previous_session_port_edit_{selected_port}"
                tag_key = f"previous_session_tag_edit_{selected_port}"
                
                col1, col2, col3 = st.columns([2, 2, 2])
                
                with col1:
                    # Editable port field - updates when dropdown changes
                    edited_port = st.number_input(
                        "Port (edit if needed)",
                        min_value=9000,
                        max_value=9100,
                        value=selected_port,
                        step=1,
                        key=port_key,
                        help="Edit the port number (9000-9100)"
                    )
                
                with col2:
                    # Check if edited port is active
                    instances = get_instances()
                    active_ports = {str(inst['port']) for inst in instances} if instances else set()
                    edited_port_is_active = str(edited_port) in active_ports
                    
                    if edited_port_is_active:
                        st.warning("⚠️ This port is currently active")
                    else:
                        st.success("✅ Port is available")
                
                with col3:
                    session_disable_timer = st.checkbox(
                        "Disable expiration timer",
                        value=False,
                        key="previous_session_disable_timer",
                        help="If enabled, the session will never expire automatically"
                    )
                    if session_disable_timer:
                        session_ttl = None
                        st.info("⏰ Timer disabled")
                    else:
                        session_ttl = st.slider(
                            "Session duration (minutes)",
                            15, 1440, 60,
                            key="previous_session_ttl"
                        )
                
                # Separate editable tag field - updates when dropdown changes
                edited_tag = st.text_input(
                    "Tag (edit if needed)",
                    value=selected_tag,
                    placeholder="e.g., My Project, Data Analysis",
                    key=tag_key,
                    help="Edit the tag for this port and click 'Update Fields' to save changes."
                )
                
                # Password field - resets when dropdown changes
                pwd_key = f"previous_session_password_{selected_port}"
                session_password = st.text_input(
                    "Set password (optional)",
                    type="password",
                    placeholder="Auto-generated if empty",
                    key=pwd_key
                )
                
                # Two buttons: Update Fields and Start Jupyter
                col_btn1, col_btn2 = st.columns([1, 1])
                
                # Dynamic keys for buttons
                update_key = f"update_fields_button_{selected_port}"
                start_key = f"open_previous_session_{selected_port}"
                
                with col_btn1:
                    if st.button("💾 Update Fields", key=update_key, use_container_width=True):
                        final_tag = edited_tag.strip() if edited_tag and edited_tag.strip() else ""
                        
                        # Update history for the edited port (which might be different from selected_port)
                        update_port_history(edited_port, final_tag)
                        
                        # If port changed, also update the old port's history (remove or keep as is)
                        if edited_port != selected_port:
                            # Keep old port history but update tag if needed
                            update_port_history(selected_port, final_tag)
                        
                        display_tag = final_tag if final_tag else "Untagged"
                        if edited_port != selected_port:
                            st.success(f"✅ Port updated to {edited_port}, Tag updated to: {display_tag}")
                        else:
                            st.success(f"✅ Tag updated to: {display_tag}")
                        st.rerun()
                
                with col_btn2:
                    if st.button("🚀 Start Jupyter", type="primary", key=start_key, use_container_width=True):
                        # Validate edited port
                        if not (9000 <= edited_port <= 9100):
                            st.error("Port must be between 9000 and 9100")
                        elif edited_port_is_active:
                            st.warning(f"Port {edited_port} is currently active. Please stop it first.")
                        else:
                            params = {
                                "user_port": int(edited_port)
                            }
                            if session_ttl is not None:
                                params["session_minutes"] = session_ttl
                            else:
                                params["disable_timer"] = True
                            if session_password:
                                params["password"] = session_password
                            
                            resp = requests.post(API_BASE, params=params)
                            if resp.status_code == 200:
                                data = resp.json()
                                actual_port = data.get('port', edited_port)
                                
                                # Update history with edited tag and port
                                final_tag = edited_tag.strip() if edited_tag and edited_tag.strip() else ""
                                update_port_history(actual_port, final_tag)
                                
                                display_tag = final_tag if final_tag else "Untagged"
                                st.success(f"Session opened on port {actual_port}!")
                                st.markdown("### 🔐 Access Details")
                                st.markdown(f"- **URL:** [{data['url']}]({data['url']})")
                                st.markdown(f"- **Password:** `{data['password']}`")
                                st.markdown(f"- **Port:** {actual_port}")
                                st.markdown(f"- **Tag:** {display_tag}")
                                if data.get('expires_at'):
                                    st.info(f"Expires at: {data['expires_at']} UTC")
                                else:
                                    st.info("⏰ Timer disabled - session will not expire automatically")
                                
                                st.rerun()
                            else:
                                error_msg = resp.json().get("detail", "Failed to start session")
                                st.error(f"Failed to open session: {error_msg}")
        else:
            st.info("No previous sessions found in history")
else:
    with st.expander("📂 Open Previously Opened Session", expanded=False):
        st.info("No previous sessions found. Start a new session to build your history.")

st.divider()

# ------------------------
# LIST RUNNING SESSIONS
# ------------------------
def get_instances():
    resp = requests.get(API_BASE)
    if resp.status_code != 200:
        st.error("Cannot reach backend")
        st.stop()
    return resp.json()
st.subheader("📋 Active Jupyter Sessions")

instances = get_instances()
now = datetime.now(timezone.utc)

if not instances:
    st.info("No running Jupyter sessions")
else:
    for inst in instances:
        expires_at_str = inst.get("expires_at")
        if expires_at_str:
            expires = datetime.fromisoformat(expires_at_str)
            remaining = expires - now
            mins_left = max(int(remaining.total_seconds() // 60), 0)
            expires_display = expires.strftime('%Y-%m-%d %H:%M:%S UTC')
            time_remaining_display = f"⏳ **{mins_left} min remaining**"
        else:
            expires = None
            expires_display = "Never (timer disabled)"
            time_remaining_display = "⏰ **No expiration**"

        with st.container():
            col1, col2, col3, col4, col5 = st.columns([1.2, 1.2, 2.5, 2, 1])
            col1.write(f"**Port**\n{inst['port']}")
            col2.write(f"**PID**\n{inst['pid']}")
            col3.write(f"**Expires**\n{expires_display}")
            col4.write(time_remaining_display)

            if col5.button("🛑 Stop", key=f"stop-{inst['port']}"):
                r = requests.delete(f"{API_BASE}/{inst['port']}")
                if r.status_code == 200:
                    st.success(f"Stopped {inst['port']}")
                else:
                    st.error("Failed to stop")

            # ---- URL + PASSWORD ----
            st.markdown(f"🔗 **URL:** [{inst['url']}]({inst['url']})")
            show_pass = st.checkbox("👁 Show password", key=f"show-{inst['port']}")
            if show_pass:
                st.text_input("Password", value=inst["password"], type="default", disabled=True, key=f"password-{inst['port']}")
            else:
                st.text_input("Password", value="************", type="password", disabled=True, key=f"password-{inst['port']}-1")

            st.divider()
