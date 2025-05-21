import streamlit as st
import pandas as pd
import os
from datetime import datetime
import time
import pickle

# --- Constants ---
REFRESH_FILE = "refresh_trigger.txt"
STATE_FILE = "streamlit_session.pkl"

def load_admin_state():
    """Load admin state from pickle file."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "rb") as f:
                admin_state = pickle.load(f)
            return admin_state
        except Exception as e:
            st.error(f"Error loading portal state: {e}")
            return None
    else:
        st.error("Portal state file not found. Please contact admin.")
        return None

def get_class_list():
    """Return a list of all classroom CSVs (without .csv extension)."""
    return [f.replace(".csv", "") for f in os.listdir() if f.endswith(".csv")]

def auto_refresh_if_needed():
    """Check the refresh trigger file and rerun if changed."""
    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = ""

    if os.path.exists(REFRESH_FILE):
        with open(REFRESH_FILE, "r") as f:
            current_value = f.read().strip()
        if current_value != st.session_state.last_refresh:
            st.session_state.last_refresh = current_value
            st.rerun()

def show_student_panel():
    st.title("📚 Student Attendance Portal")

    auto_refresh_if_needed()
    time.sleep(1)  # Allow I/O sync

    class_list = get_class_list()
    if not class_list:
        st.warning("No classrooms available. Please contact admin.")
        return

    selected_class = st.selectbox("Select Your Class", class_list)

    st.subheader("📝 Mark Your Attendance")
    with st.form("attendance_form"):
        name = st.text_input("Full Name")
        roll = st.text_input("Roll Number")
        token = st.text_input("Attendance Token")

        submit = st.form_submit_button("Submit Attendance")

        if submit:
            if not name.strip() or not roll.strip() or not token.strip():
                st.warning("All fields are required.")
                return

            admin_state = load_admin_state()
            if admin_state is None:
                return

            st.session_state.attendance_status = admin_state.get("attendance_status", {})
            st.session_state.attendance_codes = admin_state.get("attendance_codes", {})
            st.session_state.attendance_limits = admin_state.get("attendance_limits", {})

            # Check if portal is open for selected class
            if not st.session_state.attendance_status.get(selected_class, False):
                st.error("❌ Attendance portal is currently CLOSED for this class.")
                return

            expected_token = st.session_state.attendance_codes.get(selected_class, "")
            if token != expected_token:
                st.error("❌ Invalid token.")
                return

            file_path = f"{selected_class}.csv"
            if not os.path.exists(file_path):
                st.error("❌ Classroom attendance file not found. Please contact admin.")
                return

            df = pd.read_csv(file_path)

            # Token limit enforcement
            limit = st.session_state.attendance_limits.get(selected_class)
            if limit is not None and len(df) >= limit:
                st.error("❌ Token limit reached. Please contact your teacher.")
                return

            # Duplicate check
            if roll in df["Roll Number"].astype(str).values:
                st.warning("⚠️ You have already marked your attendance.")
                return

            # Append new row
            new_row = {
                "Roll Number": roll,
                "Name": name,
                "Date": datetime.now().strftime("%Y-%m-%d")
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

            # Sort by Roll Number (if numeric)
            try:
                df["Roll Number"] = df["Roll Number"].astype(int)
                df.sort_values(by="Roll Number", inplace=True)
                df["Roll Number"] = df["Roll Number"].astype(str)  # keep consistency
            except:
                df.sort_values(by="Roll Number", inplace=True)

            df.to_csv(file_path, index=False)
            st.success("✅ Attendance marked successfully!")


