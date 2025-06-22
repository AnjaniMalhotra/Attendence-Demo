# student_main.py

import streamlit as st
from student import show_student_panel
import pandas as pd
from supabase import create_client
from datetime import datetime
import pytz

def current_ist_date():
    return datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%Y-%m-%d")

# ---------- 🔐 Supabase Setup ----------
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(
    page_title="Student Dashboard",
    page_icon="🎓",
    layout="centered"
)

# ---------- Main Title ----------
st.title("🎓 Student Attendance Portal")

# ---------- Show Attendance Marking Form ----------
show_student_panel()

# ---------- Optional Attendance History Viewer ----------
st.markdown("---")
st.subheader("📅 View Your Attendance History")

with st.form("view_history_form"):
    view_class = st.selectbox("Select Class", [
        c["class_name"] for c in supabase.table("classroom_settings").select("class_name").execute().data
    ])
    view_roll = st.text_input("Enter Your Roll Number").strip()

    submit_view = st.form_submit_button("🔍 View Attendance")

    if submit_view:
        if not view_roll:
            st.warning("Please enter a roll number.")
        else:
            data = supabase.table("attendance").select("*").eq("class_name", view_class).eq("roll_number", view_roll).execute().data
            if not data:
                st.info("No attendance records found.")
            else:
                df = pd.DataFrame(data)
                df["status"] = "P"

                # Create pivot matrix
                matrix = df.pivot_table(
                    index=["roll_number", "name"],
                    columns="date",
                    values="status",
                    aggfunc="first",
                    fill_value="A"
                ).reset_index()

                matrix.columns.name = None
                matrix = matrix.sort_values("roll_number")
                st.dataframe(matrix, use_container_width=True)

                # Optional CSV Download
                csv = matrix.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="⬇️ Download Attendance Report",
                    data=csv,
                    file_name=f"{view_class}_{view_roll}_attendance.csv",
                    mime="text/csv"
                )
