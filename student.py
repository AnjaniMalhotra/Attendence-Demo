# ---------- ✅ student.py (Refactored & Styled) ----------

from datetime import datetime
import pytz
from supabase import create_client, Client
import streamlit as st

def show_student_panel():
    # ---------- 🧠 Timezone Config ----------
    IST = pytz.timezone("Asia/Kolkata")
    def current_ist_date():
        return datetime.now(IST).strftime("%Y-%m-%d")

    # ---------- 🔐 Supabase Setup ----------
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)

    # ---------- 🎓 UI ----------
    st.title("🎓 Student Attendance Portal")

    # ---------- 📘 Load Open Classes ----------
    open_classes_response = supabase.table("classroom_settings") \
        .select("class_name").eq("is_open", True).execute()

    class_list = [entry["class_name"] for entry in open_classes_response.data]

    if not class_list:
        st.warning("🚫 No classrooms are currently open for attendance.")
        return

    selected_class = st.selectbox("Select Your Class", class_list)

    # ---------- ⚙️ Class Settings ----------
    settings = supabase.table("classroom_settings") \
        .select("code", "daily_limit").eq("class_name", selected_class) \
        .execute().data[0]

    required_code = settings["code"]
    daily_limit = settings["daily_limit"]

    # ---------- 🧠 Roll Number ----------
    roll_number = st.text_input("🔢 Roll Number").strip()

    if not roll_number:
        return

    # ---------- 🔐 Name Locking ----------
    roll_map = supabase.table("roll_map").select("name") \
        .eq("class_name", selected_class).eq("roll_number", roll_number).execute()

    if roll_map.data:
        name = roll_map.data[0]["name"]
        st.success(f"🔒 Name auto-filled for Roll `{roll_number}`: **{name}**")
    else:
        name = st.text_input("👤 Name (Will be locked after first time)").strip()

    code_input = st.text_input("🛡️ Attendance Code", type="password")

    # ---------- ✅ Submit Attendance ----------
    if st.button("✅ Submit Attendance"):
        today = current_ist_date()

        # Validate code
        if code_input != required_code:
            st.error("❌ Incorrect attendance code.")
            return

        # Check if already marked
        already_marked = supabase.table("attendance").select("*") \
            .eq("class_name", selected_class).eq("roll_number", roll_number) \
            .eq("date", today).execute().data

        if already_marked:
            st.warning("📌 You have already marked attendance for today.")
            return

        # Check daily limit
        attendance_today = supabase.table("attendance").select("*", count="exact") \
            .eq("class_name", selected_class).eq("date", today).execute()

        if (attendance_today.count or 0) >= daily_limit:
            st.warning("⚠️ Attendance limit for today has been reached.")
            return

        # Lock name if first-time entry
        if not roll_map.data:
            supabase.table("roll_map").insert({
                "class_name": selected_class,
                "roll_number": roll_number,
                "name": name
            }).execute()
        else:
            if name != roll_map.data[0]["name"]:
                st.error("❌ Roll number already locked to a different name.")
                return

        # Insert attendance
        supabase.table("attendance").insert({
            "class_name": selected_class,
            "roll_number": roll_number,
            "name": name,
            "date": today
        }).execute()

        st.success("✅ Attendance submitted successfully!")
