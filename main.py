# ---------- ✅ main.py (Final Version with Enhanced State Initialization) ----------

import streamlit as st
from admin import show_admin_panel
from student import show_student_panel
import os
import pickle

# ----- Page Configuration -----
st.set_page_config(page_title="Smart Attendance System", layout="centered")

# ----- State File and Shared Keys -----
STATE_FILE = "streamlit_session.pkl"
shared_keys = [
    "attendance_status",
    "attendance_codes",
    "attendance_limits",
    "submitted_rolls",
    "roll_name_map"
]

# ----- Load Persistent State from Pickle File if Exists -----
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "rb") as f:
        loaded_state = pickle.load(f)
    for key in shared_keys:
        if key in loaded_state:
            st.session_state[key] = loaded_state[key]

# ----- Ensure State Keys Exist in Session -----
for key in shared_keys:
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
