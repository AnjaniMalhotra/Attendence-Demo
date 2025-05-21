import streamlit as st
import os
import pandas as pd
from datetime import datetime
import pickle

# ---- Admin credentials ----



STATE_FILE = "streamlit_session.pkl"

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
        with open(STATE_FILE, "rb") as f:
            admin_state = pickle.load(f)
        return admin_state
    else:
        # Return empty dicts if no saved state
        return {
            "attendance_status": {},
            "attendance_codes": {},
            "attendance_limits": {}
        }
ADMIN_USERNAME = "admin"
def get_class_list():
    """Return a list of all classroom CSVs (without .csv extension)."""
    files = [f.replace(".csv", "") for f in os.listdir() if f.endswith(".csv")]
    return files

def create_classroom(class_name):
    """Create a new classroom CSV file with headers if it doesn't exist."""
    file_path = f"{class_name}.csv"
    if not os.path.exists(file_path):
        df = pd.DataFrame(columns=["Roll Number", "Name", "Timestamp"])
        df.to_csv(file_path, index=False)

def delete_classroom(class_name):
    """Delete a classroom CSV file."""
    file_path = f"{class_name}.csv"
    if os.path.exists(file_path):
        os.remove(file_path)

def trigger_student_refresh():
    """Update the refresh trigger file to notify students to reload their session."""
    with open("refresh_trigger.txt", "w") as f:
        f.write(datetime.now().isoformat())
ADMIN_PASSWORD = "admin123"
def show_admin_panel():
    st.title("Admin Panel")

    # --- Login Form ---
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        st.subheader("Admin Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                
                # Load saved state on login
                admin_state = load_admin_state()
                st.session_state.attendance_status = admin_state.get("attendance_status", {})
                st.session_state.attendance_codes = admin_state.get("attendance_codes", {})
                st.session_state.attendance_limits = admin_state.get("attendance_limits", {})

                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials")
        return

    # --- Initialize Session Variables if not present ---
    if "attendance_status" not in st.session_state:
        st.session_state.attendance_status = {}
    if "attendance_codes" not in st.session_state:
        st.session_state.attendance_codes = {}
    if "attendance_limits" not in st.session_state:
        st.session_state.attendance_limits = {}

    # --- Classroom Management ---
    st.subheader("Manage Classrooms")

    col1, col2 = st.columns([2, 1])
    with col1:
        new_class = st.text_input("Add New Classroom (e.g., class_10A)")
    with col2:
        if st.button("Add Classroom") and new_class:
            create_classroom(new_class)
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

    # --- Attendance Control ---
    st.subheader("Attendance Control")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Open Attendance"):
            st.session_state.attendance_status[selected_class] = True
            save_admin_state()
            trigger_student_refresh()
            st.success(f"Attendance portal for {selected_class} is OPEN.")

    with col2:
        if st.button("Close Attendance"):
            st.session_state.attendance_status[selected_class] = False
            save_admin_state()
            trigger_student_refresh()
            st.info(f"Attendance portal for {selected_class} is CLOSED.")

    # Set token/code and token limit
    code = st.text_input("Set Attendance Code", key=f"code_{selected_class}")
    limit = st.number_input("Limit number of students allowed to mark attendance", min_value=1, step=1, key=f"limit_{selected_class}")

    if st.button("Update Code & Limit"):
        st.session_state.attendance_codes[selected_class] = code
        st.session_state.attendance_limits[selected_class] = limit
        save_admin_state()
        st.success(f"Code and token limit updated for {selected_class}")

    st.markdown("---")

    # --- View Attendance ---
    st.subheader(f"Attendance for {selected_class}")
    if os.path.exists(f"{selected_class}.csv"):
        df = pd.read_csv(f"{selected_class}.csv")
        st.dataframe(df)

        st.download_button(
            "Download Attendance CSV",
            df.to_csv(index=False),
            file_name=f"{selected_class}.csv"
        )
    else:
        st.warning(f"No data found for {selected_class}")
