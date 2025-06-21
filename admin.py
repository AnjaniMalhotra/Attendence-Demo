import streamlit as st
from supabase_client import supabase

def show_admin_panel():
    st.subheader("🧑‍🏫 Admin Panel")

    class_name = st.text_input("Enter Class Name")
    code = st.text_input("Set Attendance Code")
    daily_limit = st.number_input("Set Daily Limit", min_value=1, value=10)
    status = st.selectbox("Attendance Status", ["Open", "Closed"])

    if st.button("Save / Update Classroom"):
        supabase.table("classroom_settings").upsert({
            "class_name": class_name,
            "code": code,
            "daily_limit": daily_limit,
            "status": status == "Open"
        }).execute()
        st.success("✅ Classroom settings saved.")

    st.markdown("---")
    st.subheader("📊 View Attendance")
    if class_name:
        result = supabase.table("attendance_records").select("*").eq("class_name", class_name).order("submitted_at", desc=True).execute()
        data = result.data
        if data:
            st.dataframe(data)
        else:
            st.info("No attendance data for this class yet.")
