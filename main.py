import streamlit as st
from admin import show_admin_panel
from student import show_student_panel
import os

# ----- Page Configuration -----
st.set_page_config(page_title="Smart Attendance System", layout="centered")

# ----- Initialize Shared Session State -----
for key in ["attendance_status", "attendance_codes", "attendance_limits"]:
    if key not in st.session_state:
        st.session_state[key] = {}

# ----- Ensure Refresh Trigger File Exists -----
REFRESH_FILE = "refresh_trigger.txt"
if not os.path.exists(REFRESH_FILE):
    with open(REFRESH_FILE, "w") as f:
        f.write("init")

# ----- App Title -----
st.title("📘 Smart Attendance System")

# ----- Tabs for Role-Based Panels -----
tab1, tab2 = st.tabs(["🧑‍🏫 Admin Panel", "🎓 Student Panel"])

with tab1:
    show_admin_panel()

with tab2:
    show_student_panel()
