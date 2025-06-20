import streamlit as st
import pandas as pd
import os
from datetime import datetime

def show_student_panel():
    st.header("🎓 Student Panel")

    class_files = [f for f in os.listdir() if f.endswith(".csv") and not f.startswith("streamlit_session")]

    if not class_files:
        st.warning("No classes found. Please check with the admin.")
        return

    selected_class = st.selectbox("Select Your Class", [f.replace(".csv", "") for f in class_files])

    if not selected_class:
        st.info("Please select a class to mark attendance.")
        return

    # Check if attendance is open
    if selected_class not in st.session_state.attendance_status or not st.session_state.attendance_status[selected_class]:
        st.warning(f"Attendance for '{selected_class}' is currently CLOSED.")
        return

    st.success(f"Attendance for '{selected_class}' is OPEN.")

    roll_no = st.text_input("Enter Roll Number")
    name = st.text_input("Enter Full Name")
    code = st.text_input("Enter Attendance Code", type="password")

    if st.button("Submit Attendance"):
        if not roll_no or not name or not code:
            st.warning("Please fill all the fields.")
            return

        expected_code = st.session_state.attendance_codes.get(selected_class, "")
        if code != expected_code:
            st.error("Invalid Attendance Code.")
            return

        limit = st.session_state.attendance_limits.get(selected_class, 1)
        file_path = f"{selected_class}.csv"
        now = datetime.now().strftime("%Y-%m-%d")

        try:
            df = pd.read_csv(file_path)
        except Exception:
            df = pd.DataFrame(columns=["Roll Number", "Name"])

        # Add date column if it doesn’t exist
        if now not in df.columns:
            df[now] = ""

        # Check existing entries
        existing = df[(df["Roll Number"] == roll_no) & (df["Name"] == name)]

        if not existing.empty and df.loc[existing.index[0], now] == "✓":
            st.info("Attendance already marked.")
            return

        if len(df[df[now] == "✓"]) >= limit:
            st.error("Attendance limit reached.")
            return

        # Mark attendance
        if existing.empty:
            new_row = {"Roll Number": roll_no, "Name": name, now: "✓"}
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        else:
            df.loc[existing.index[0], now] = "✓"

        df.to_csv(file_path, index=False)
        st.success("Attendance submitted successfully.")
