# ---------- ✅ main.py (Sidebar Version - Fully Compatible) ----------

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

# ----- Sidebar Navigation for Role-Based Panels -----
st.sidebar.title("🔍 Navigation")
panel = st.sidebar.radio("Choose Panel", ["Admin Panel", "Student Panel"])

st.title("📘 Smart Attendance System")

if panel == "Admin Panel":
    show_admin_panel()
else:
    show_student_panel()
