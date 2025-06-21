# ---------- ✅ main.py (Supabase + Streamlit + Tabs UI) ----------

import streamlit as st
from admin import show_admin_panel
from student import show_student_panel

# Page Config
st.set_page_config(
    page_title="Smart Attendance System",
    layout="centered",
    page_icon="🧠"
)

# App Title
st.title("🧠 Smart Attendance System (Supabase)")

# Role Tabs
admin_tab, student_tab = st.tabs(["🧑‍🏫 Admin Panel", "🎓 Student Panel"])

with admin_tab:
    show_admin_panel()

with student_tab:
    show_student_panel()
