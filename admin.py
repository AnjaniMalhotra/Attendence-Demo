import streamlit as st
import os
import pandas as pd
from datetime import datetime
import pickle

# ---- Admin credentials ----
ADMIN_USERNAME = st.secrets["ADMIN_USERNAME"]
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]

STATE_FILE = "streamlit_session.pkl"
CSV_DIR = "class_data"  # Folder for all classroom CSVs

# Ensure the directory exists
os.makedirs(CSV_DIR, exist_ok=True)

# ---- Helper Functions ----

def save_admin_state():
    admin_state = {
        "attendance_status": st.session_state.attendance_status,
        "attendance_codes": st.session_state.attendance_codes,
        "attendance_limits": st.session_state.attendance_limits
    }
    with open(STATE_FILE, "wb") as f:
        pickle.dump(admin_state, f)

def load_admin_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            st.error(f"Error loading admin state: {e}")
            return {"attendance_status": {}, "attendance_codes": {}, "attendance_limits": {}}
    else:
        return {"attendance_status": {}, "attendance_codes": {}, "attendance_limits": {}}

def get_class_list():
    return [f.replace(".csv", "") for f in os.listdir(CSV_DIR) if f.endswith(".csv")]

def create_classroom(class_name):
    file_path = os.path.join(CSV_DIR, f"{class_name}.csv")
    if not os.path.exists(file_path):
        df = pd.DataFrame(columns=["Roll Number", "Name"])
        df.to_csv(file_path, index=False)

def delete_classroom(class_name):
    file_path = os.path.join(CSV_DIR, f"{class_name}.csv")
    if os.path.exists(file_path):
        os.remove(file_path)
        st.session_state.attendance_status.pop(class_name, None)
        st.session_state.attendance_codes.pop(class_name, None)
        st.session_state.attendance_limits.pop(class_name, None)
        save_admin_state()

def trigger_student_refresh():
    with open("refresh_trigger.txt", "w") as f:
        f.write(datetime.now().isoformat())

def show_admin_panel():
    st.title("Admin Panel")

    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        st.subheader("Admin Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                admin_state = load_admin_state()
                st.session_state.attendance_status = admin_state.get("attendance_status", {})
                st.session_state.attendance_codes = admin_state.get("attendance_codes", {})
                st.session_state.attendance_limits = admin_state.get("attendance_limits", {})
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials")
        return

    if st.sidebar.button("Logout Admin"):
        st.session_state.admin_logged_in = False
        st.rerun()

    if "attendance_status" not in st.session_state:
        st.session_state.attendance_status = {}
    if "attendance_codes" not in st.session_state:
        st.session_state.attendance_codes = {}
    if "attendance_limits" not in st.session_state:
        st.session_state.attendance_limits = {}

    st.subheader("Manage Classrooms")
    col1, col2 = st.columns([2, 1])
    with col1:
        new_class = st.text_input("Add New Classroom (e.g., class_10A)")
    with col2:
        if st.button("Add Classroom"):
            if not new_class.strip():
                st.warning("Classroom name cannot be empty.")
            elif new_class.strip() in get_class_list():
                st.warning(f"Classroom '{new_class}' already exists.")
            else:
                create_classroom(new_class.strip())
                st.success(f"Classroom '{new_class}' created.")
                st.rerun()

    class_list = get_class_list()
    if not class_list:
        st.warning("No classrooms found. Please add a classroom.")
        return

    selected_class = st.selectbox("Select Classroom", class_list)

    if st.button("Delete Selected Classroom"):
        delete_classroom(selected_class)
        st.warning(f"Classroom '{selected_class}' deleted.")
        st.rerun()

    st.markdown("---")

    st.subheader(f"Attendance Control for '{selected_class}'")
    current_status = st.session_state.attendance_status.get(selected_class, False)
    status_text = "OPEN" if current_status else "CLOSED"
    st.info(f"Current Attendance Status: **{status_text}**")

    col_open, col_close = st.columns(2)
    with col_open:
        if st.button("Open Attendance"):
            st.session_state.attendance_status[selected_class] = True
            save_admin_state()
            trigger_student_refresh()
            st.success(f"Attendance portal for {selected_class} is OPEN.")
            st.rerun()
    with col_close:
        if st.button("Close Attendance"):
            st.session_state.attendance_status[selected_class] = False
            save_admin_state()
            trigger_student_refresh()
            st.info(f"Attendance portal for {selected_class} is CLOSED.")
            st.rerun()

    current_code = st.session_state.attendance_codes.get(selected_class, "")
    current_limit = st.session_state.attendance_limits.get(selected_class, 1)

    st.markdown(f"**Current Code:** `{current_code}`")
    st.markdown(f"**Current Limit:** `{current_limit}`")

    code = st.text_input("Set New Attendance Code", value=current_code)
    limit = st.number_input("Set Token Limit", min_value=1, value=current_limit, step=1)

    if st.button("Update Code & Limit"):
        st.session_state.attendance_codes[selected_class] = code
        st.session_state.attendance_limits[selected_class] = int(limit)
        save_admin_state()
        st.success(f"Code and token limit updated for {selected_class}")
        st.rerun()

    st.markdown("---")
    st.subheader(f"Attendance for {selected_class}")
    
    file_path = os.path.join(CSV_DIR, f"{selected_class}.csv")
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            if df.empty:
                st.info("No attendance recorded yet.")
            else:
                st.dataframe(df)
                st.download_button(
                    "Download Attendance CSV",
                    df.to_csv(index=False).encode('utf-8'),
                    file_name=f"attendance_{selected_class}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        except Exception as e:
            st.error(f"Error reading file: {e}")
    else:
        st.warning(f"No file found for {selected_class}.")
