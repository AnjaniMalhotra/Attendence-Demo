import streamlit as st
from supabase_client import supabase
from datetime import datetime
import pytz

def current_ist_date():
    return datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%Y-%m-%d")

def show_student_panel():
    st.subheader("🎓 Student Panel")

    class_name = st.text_input("Enter Class Name")
    roll_number = st.text_input("Roll Number")
    name = st.text_input("Your Name")
    code_input = st.text_input("Attendance Code")

    if st.button("Submit Attendance"):
        today = current_ist_date()

        # Fetch classroom config
        res = supabase.table("classroom_settings").select("*").eq("class_name", class_name).execute()
        if not res.data:
            st.error("⚠️ Class does not exist.")
            return

        config = res.data[0]
        if not config["status"]:
            st.warning("🚫 Attendance is currently closed.")
            return

        if code_input != config["code"]:
            st.error("❌ Incorrect code.")
            return

        # Check if already submitted
        check = supabase.table("attendance_records")\
            .select("*")\
            .eq("class_name", class_name)\
            .eq("roll_number", roll_number)\
            .eq("date", today).execute()

        if check.data:
            st.warning("⚠️ Attendance already submitted for today.")
            return

        # Check daily limit
        today_count = supabase.table("attendance_records")\
            .select("*")\
            .eq("class_name", class_name)\
            .eq("date", today).execute()

        if len(today_count.data) >= config["daily_limit"]:
            st.warning("⚠️ Attendance limit reached.")
            return

        # Submit attendance
        supabase.table("attendance_records").insert({
            "class_name": class_name,
            "roll_number": roll_number,
            "name": name,
            "date": today
        }).execute()
        st.success("✅ Attendance submitted successfully.")
