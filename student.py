# ---------- ✅ student.py (Supabase + Proxy-Proof + One-Time Name Entry + Class Specific Table) ----------

import streamlit as st
import pandas as pd
import pytz
from datetime import datetime
from supabase import create_client

# --- Timezone Setup ---
IST = pytz.timezone('Asia/Kolkata')
def current_ist_date():
    return datetime.now(IST).strftime("%Y-%m-%d")

# --- Supabase Credentials ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def show_student_panel():
    st.header("🎓 Student Attendance")

    # Get only open classrooms
    class_data = supabase.table("classroom_settings").select("*").eq("is_open", True).execute()
    if not class_data.data:
        st.warning("No open classrooms currently.")
        return

    class_names = [cls["class_name"] for cls in class_data.data]
    selected_class = st.selectbox("Select Your Class", class_names)

    class_row = next(cls for cls in class_data.data if cls["class_name"] == selected_class)
    code_required = class_row.get("code", "")
    limit = class_row.get("limit", 1)
    table_name = f"attendance_{selected_class.replace(' ', '_')}"

    roll_number = st.text_input("Roll Number", key="roll")
    name = ""

    # Check if name exists for this roll_number in this class
    if roll_number:
        try:
            existing_entries = supabase.table(table_name).select("name").eq("roll_number", roll_number).execute().data
            if existing_entries:
                name = existing_entries[0]["name"]
                st.info(f"📝 Name auto-filled for roll {roll_number}: {name}")
            else:
                name = st.text_input("Name", key="name")
        except Exception as e:
            st.error(f"Error checking roll number: {e}")
            return

    code_input = st.text_input("Attendance Code", key="code")

    if st.button("Submit Attendance"):
        if not roll_number:
            st.error("Roll number is required.")
        elif not name:
            st.error("Name is required.")
        elif code_input != code_required:
            st.error("❌ Invalid Code.")
        else:
            today = current_ist_date()

            try:
                # Check if already marked today
                entries_today = supabase.table(table_name).select("*").eq("roll_number", roll_number).eq("date", today).execute().data
                if entries_today:
                    st.warning("⚠️ You have already marked attendance today.")
                    return

                # Check today's attendance count
                todays_count = supabase.table(table_name).select("*", count="exact").eq("date", today).execute().count
                if todays_count >= limit:
                    st.warning("⚠️ Attendance limit reached for today.")
                    return

                # Submit attendance
                supabase.table(table_name).insert({
                    "roll_number": roll_number,
                    "name": name,
                    "date": today
                }).execute()

                st.success("✅ Attendance submitted successfully!")

            except Exception as e:
                st.error(f"Submission failed: {e}")
