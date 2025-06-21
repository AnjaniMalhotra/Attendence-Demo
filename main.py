# ---------- ✅ main.py (Supabase + Streamlit Attendance App) ----------

import streamlit as st
from admin import show_admin_panel
from student import show_student_panel

st.set_page_config(page_title="Supabase Attendance System", layout="centered")

# Sidebar Navigation
st.sidebar.title("📚 Navigation")
mode = st.sidebar.radio("Choose Mode", ["Student Panel", "Admin Panel"])

st.title("🧠 Smart Attendance System (Supabase)")

if mode == "Admin Panel":
    show_admin_panel()
else:
    show_student_panel()
