# ---------- ✅ main.py (Supabase + Streamlit + Tabs UI) ----------

import streamlit as st
from admin import show_admin_panel
from student import show_student_panel

# ---------- 🎨 Page Config ----------
st.set_page_config(
    page_title="Smart Attendance System",
    page_icon="🧠",
    layout="centered"
)

# ---------- 🧠 App Title ----------
st.markdown(
    """
    <h1 style='text-align: center; color: #4B8BBE;'>🧠 Smart Attendance System</h1>
    
    <hr style='border-top: 1px solid #bbb;'/>
    """,
    unsafe_allow_html=True
)

# ---------- 🔄 Role-Based Tabs ----------
admin_tab = st.tabs(["🧑‍🏫 Admin Panel"])

if __name__ == "__main__":
    show_admin_panel()

