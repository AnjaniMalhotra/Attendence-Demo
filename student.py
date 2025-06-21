# ---------- ✅ student.py (Proxy-Proof, Key-Safe, Timezone IST) ----------

import streamlit as st
import pandas as pd
import os
from datetime import datetime
import pytz
from supabase import create_client
from dotenv import load_dotenv

# Load Supabase credentials
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# IST time
IST = pytz.timezone("Asia/Kolkata")
def current_ist_date():
    return datetime.now(IST).strftime("%Y-%m-%d")

def show_student_panel():
    st.title("🎓 Student Attendance")

    # Get available classes
    res = supabase.table("classroom_settings").select("class_name").execute()
    class_list = [row["class_name"] for row in res.data]

    if not class_list:
        st.warning("No classrooms available.")
        return

    selected_class = st.selectbox("Select Your Class", class_list, key="class_selector")

    # Fetch classroom config
    config = supabase.table("classroom_settings").select("*").eq("class_name", selected_class).single().execute().data

    if not config["is_open"]:
        st.error(f"Attendance for '{selected_class}' is currently CLOSED.")
        return

    attendance_code = config["code"]
    daily_limit = config["daily_limit"]

    # Input fields
    roll_number = st.text_input("Roll Number", key="roll_input")
    name_input = st.text_input("Name", key="name_input")
    code_input = st.text_input("Attendance Code", key="code_input")

    # Auto-fetch previous name if roll already exists
    name_db = supabase.table("roll_map").select("*").eq("class_name", selected_class).eq("roll_number", roll_number).execute().data
    if name_db:
        locked_name = name_db[0]["name"]
        st.info(f"✅ Name auto-filled for Roll {roll_number}: {locked_name}")
        name = locked_name
    else:
        name = name_input

    if st.button("📌 Submit Attendance", key="submit_button"):
        if code_input != attendance_code:
            st.error("❌ Invalid Code.")
            return

        # Check if already marked today
        existing = supabase.table("attendance").select("*") \
            .eq("class_name", selected_class) \
            .eq("roll_number", roll_number) \
            .eq("date", current_ist_date()) \
            .execute().data

        if existing:
            st.error("❌ Attendance already submitted for today.")
            return

        # Enforce name locking
        if name_db and name_input and name_input != name_db[0]["name"]:
            st.error("❌ Name mismatch with registered roll number.")
            return

        if not name:
            st.error("❌ Name is required.")
            return

        # Check limit
        today_count = supabase.table("attendance").select("id", count="exact") \
            .eq("class_name", selected_class) \
            .eq("date", current_ist_date()) \
            .execute().count

        if today_count >= daily_limit:
            st.warning("⚠️ Attendance limit reached.")
            return

        # Save name lock if first time
        if not name_db:
            supabase.table("roll_map").insert({
                "class_name": selected_class,
                "roll_number": roll_number,
                "name": name
            }).execute()

        # Save attendance
        supabase.table("attendance").insert({
            "class_name": selected_class,
            "roll_number": roll_number,
            "name": name,
            "date": current_ist_date()
        }).execute()

        st.success("✅ Attendance marked successfully!")
