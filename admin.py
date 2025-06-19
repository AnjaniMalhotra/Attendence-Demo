import streamlit as st
import gspread
import pandas as pd
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
import pickle
import os

# ---- Credentials ----
ADMIN_USERNAME = st.secrets["ADMIN"]["ADMIN_USERNAME"]
ADMIN_PASSWORD = st.secrets["ADMIN"]["ADMIN_PASSWORD"]

# ---- Google Sheets Setup ----
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = dict(st.secrets["gspread"])
credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(credentials)

SHEET_NAME = "Attendance"
STATE_FILE = "streamlit_session.pkl"

# ---- Google Sheets Helpers ----

def get_worksheet(class_name):
    try:
        sh = client.open(SHEET_NAME)
        return sh.worksheet(class_name)
    except:
        return None

def create_classroom(class_name):
    sh = client.open(SHEET_NAME)
    try:
        sh.add_worksheet(title=class_name, rows="100", cols="20")
        ws = sh.worksheet(class_name)
        ws.append_row(["Roll Number", "Name"])  # headers
    except Exception as e:
        st.error(f"Error creating class: {e}")

def delete_classroom(class_name):
    sh = client.open(SHEET_NAME)
    try:
        sh.del_worksheet(sh.worksheet(class_name))
        for key in ["attendance_status", "attendance_codes", "attendance_limits"]:
            st.session_state[key].pop(class_name, None)
        save_admin_state()
    except Exception as e:
        st.error(f"Error deleting class: {e}")

def get_class_list():
    sh = client.open(SHEET_NAME)
    return [ws.title for ws in sh.worksheets()]

def get_attendance_df(class_name):
    ws = get_worksheet(class_name)
    data = ws.get_all_records()
    return pd.DataFrame(data)

def update_attendance_df(class_name, df):
    ws = get_worksheet(class_name)
    ws.clear()
    ws.update([df.columns.tolist()] + df.values.tolist())

# ---- Session Persistence ----
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
        with open(STATE_FILE, "rb") as f:
            return pickle.load(f)
    return {"attendance_status": {}, "attendance_codes": {}, "attendance_limits": {}}

def trigger_student_refresh():
    with open("refresh_trigger.txt", "w") as f:
        f.write(datetime.now().isoformat())

# ---- UI Logic ----
def show_admin_panel():
    st.title("Admin Panel")

    # --- Login ---
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        st.subheader("Admin Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                state = load_admin_state()
                st.session_state.attendance_status = state["attendance_status"]
                st.session_state.attendance_codes = state["attendance_codes"]
                st.session_state.attendance_limits = state["attendance_limits"]
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Invalid credentials")
        return

    # --- Logout ---
    if st.sidebar.button("Logout Admin"):
        st.session_state.admin_logged_in = False
        st.rerun()

    # --- State Initialization ---
    for key in ["attendance_status", "attendance_codes", "attendance_limits"]:
        if key not in st.session_state:
            st.session_state[key] = {}

    # --- Classroom Management ---
    st.subheader("Manage Classrooms")
    col1, col2 = st.columns([3, 1])
    with col1:
        new_class = st.text_input("Enter New Classroom Name (e.g., class_10A)")
    with col2:
        if st.button("Add Classroom"):
            if new_class.strip() in get_class_list():
                st.warning("Classroom already exists.")
            else:
                create_classroom(new_class.strip())
                st.success(f"Created classroom {new_class}")
                st.rerun()

    class_list = get_class_list()
    if not class_list:
        st.warning("No classrooms found.")
        return

    selected_class = st.selectbox("Select Classroom", class_list)

    if st.button("Delete Selected Classroom"):
        delete_classroom(selected_class)
        st.success(f"Deleted classroom {selected_class}")
        st.rerun()

    st.markdown("---")
    st.subheader(f"Attendance Control for {selected_class}")

    # --- Attendance Control ---
    current_status = st.session_state.attendance_status.get(selected_class, False)
    st.info(f"Current status: **{'OPEN' if current_status else 'CLOSED'}**")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Open Attendance"):
            st.session_state.attendance_status[selected_class] = True
            save_admin_state()
            trigger_student_refresh()
            st.success("Attendance opened")
            st.rerun()
    with col2:
        if st.button("Close Attendance"):
            st.session_state.attendance_status[selected_class] = False
            save_admin_state()
            trigger_student_refresh()
            st.info("Attendance closed")
            st.rerun()

    code = st.text_input("Set Attendance Code", value=st.session_state.attendance_codes.get(selected_class, ""))
    limit = st.number_input("Set Limit", value=st.session_state.attendance_limits.get(selected_class, 1), min_value=1)

    if st.button("Update Code & Limit"):
        st.session_state.attendance_codes[selected_class] = code
        st.session_state.attendance_limits[selected_class] = int(limit)
        save_admin_state()
        st.success("Updated code and limit")
        st.rerun()

    st.markdown("---")
    st.subheader(f"Attendance Records for {selected_class}")

    try:
        df = get_attendance_df(selected_class)
        if df.empty:
            st.info("No attendance recorded yet.")
        else:
            st.dataframe(df)
            st.download_button("Download CSV", df.to_csv(index=False).encode('utf-8'),
                               file_name=f"{selected_class}_{datetime.now().date()}.csv", mime="text/csv")
    except Exception as e:
        st.error(f"Error loading attendance: {e}")


# Run the Admin Panel
show_admin_panel()
