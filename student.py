import streamlit as st
import pandas as pd
import os
from datetime import datetime
import hashlib

CSV_DIR = "class_data"
os.makedirs(CSV_DIR, exist_ok=True)

# --- Helper Functions ---
def get_class_list():
    return [f.replace(".csv", "") for f in os.listdir(CSV_DIR) if f.endswith(".csv")]

def get_file_path(class_name):
    return os.path.join(CSV_DIR, f"{class_name}.csv")

def validate_code(class_name, code):
    return st.session_state.attendance_codes.get(class_name, "") == code

def is_portal_open(class_name):
    return st.session_state.attendance_status.get(class_name, False)

def has_already_marked_attendance(df, roll):
    return roll in df['Roll Number'].values

def record_attendance(class_name, roll, name):
    file_path = get_file_path(class_name)
    df = pd.read_csv(file_path)

    today = datetime.now().strftime("%Y-%m-%d")
    if today not in df.columns:
        df[today] = ""

    if roll not in df['Roll Number'].values:
        new_row = {"Roll Number": roll, "Name": name, today: "Present"}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    else:
        df.loc[df['Roll Number'] == roll, today] = "Present"

    df.to_csv(file_path, index=False)
    return True

# --- Streamlit App ---
def show_student_portal():
    st.title("Student Attendance Portal")

    if "attendance_status" not in st.session_state:
        st.session_state.attendance_status = {}
    if "attendance_codes" not in st.session_state:
        st.session_state.attendance_codes = {}
    if "attendance_limits" not in st.session_state:
        st.session_state.attendance_limits = {}

    class_list = get_class_list()
    if not class_list:
        st.warning("No classes available. Please contact your admin.")
        return

    selected_class = st.selectbox("Select your class", class_list)

    roll = st.text_input("Roll Number")
    name = st.text_input("Name")
    code = st.text_input("Attendance Code")

    if st.button("Submit Attendance"):
        if not is_portal_open(selected_class):
            st.error("Attendance portal is closed for this class.")
            return

        if not validate_code(selected_class, code):
            st.error("Invalid attendance code.")
            return

        file_path = get_file_path(selected_class)
        df = pd.read_csv(file_path)

        if has_already_marked_attendance(df, roll):
            st.warning("You have already marked attendance today.")
        else:
            if record_attendance(selected_class, roll, name):
                st.success("Attendance recorded successfully!")
            else:
                st.error("Failed to record attendance. Try again.")
