import streamlit as st
from supabase import create_client
from datetime import datetime
import pytz

# Timezone
IST = pytz.timezone("Asia/Kolkata")
def current_ist_date():
    return datetime.now(IST).strftime("%Y-%m-%d")

# Supabase
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def show_student_panel():
    st.header("🎓 Student Attendance")

    # Get all open classes
    class_data = supabase.table("classroom_settings").select("*").eq("is_open", True).execute()
    if not class_data.data:
        st.warning("No open classes at the moment.")
        return

    open_classes = [cls["class_name"] for cls in class_data.data]
    selected_class = st.selectbox("Select Your Class", open_classes)

    selected_info = next((cls for cls in class_data.data if cls["class_name"] == selected_class), None)
    code_required = selected_info.get("code", "")
    limit = selected_info.get("limit", 1)
    table_name = f"attendance_{selected_class.replace(' ', '_')}"

    # Input fields
    roll = st.text_input("Roll Number", key="roll")
    existing_name_data = supabase.table(table_name).select("name").eq("roll_number", roll).limit(1).execute()
    
    if existing_name_data.data:
        name = existing_name_data.data[0]["name"]
        st.info(f"Name auto-filled for Roll {roll}: **{name}**")
    else:
        name = st.text_input("Name", key="name")

    code_input = st.text_input("Attendance Code", type="password")

    # Submit attendance
    if st.button("Submit Attendance"):
        if not roll or not name:
            st.error("Name and roll number are required.")
            return

        if code_input != code_required:
            st.error("❌ Invalid code.")
            return

        # Check if this roll has already marked today
        today = current_ist_date()
        existing_today = supabase.table(table_name).select("*").eq("roll_number", roll).eq("date", today).execute()
        if existing_today.data:
            st.error("❌ Attendance already marked today.")
            return

        # Check roll->name consistency
        if existing_name_data.data and existing_name_data.data[0]["name"] != name:
            st.error("❌ This roll number is already registered with another name.")
            return

        # Check if attendance count for today >= limit
        count_today = supabase.table(table_name).select("id", count="exact").eq("date", today).execute().count or 0
        if count_today >= limit:
            st.warning("⚠️ Attendance limit for today reached.")
            return

        # All good, insert attendance
        supabase.table(table_name).insert({
            "roll_number": roll,
            "name": name,
            "date": today
        }).execute()
        st.success("✅ Attendance submitted!")
