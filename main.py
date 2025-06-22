# ---------- ✅ main.py (Admin + Analytics Tabs) ----------

import streamlit as st
from admin import show_admin_panel
from analytics import show_analytics_panel  # 📊 Add this

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
admin_tab, analytics_tab = st.tabs(["🧑‍🏫 Admin Panel", "📊 Analytics"])

with admin_tab:
    show_admin_panel()

with analytics_tab:
    show_analytics_panel()
