import streamlit as st
from supabase_client import supabase
import pytz
from datetime import datetime
import pandas as pd
from github import Github

# Timezone setup
IST = pytz.timezone("Asia/Kolkata")

def show_admin_panel():
    st.title("🧑‍🏫 Admin Panel")

    # Authentication
    if "admin_auth" not in st.session_state:
        st.session_state.admin_auth = False

    if not st.session_state.admin_auth:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            if u == st.secrets["ADMIN_USERNAME"] and p == st.secrets["ADMIN_PASSWORD"]:
                st.session_state.admin_auth = True
            else:
                st.error("Invalid credentials")
        return

    # Admin Controls
    st.subheader("Classroom Settings")
    class_name = st.text_input("Class Name")
    code = st.text_input("Attendance Code")
    daily_limit = st.number_input("Daily Limit", min_value=1, value=10)
    open_now = st.checkbox("Open Attendance")

    if st.button("Save Settings"):
        supabase.table("classroom_settings").upsert({
            "class_name": class_name,
            "code": code,
            "daily_limit": daily_limit,
            "is_open": open_now
        }).execute()
        st.success("✅ Settings saved")

    # Only one class open at a time
    if open_now:
        supabase.table("classroom_settings")\
            .update({"is_open": False})\
            .neq("class_name", class_name)\
            .execute()

    # Attendance Records Section
    st.markdown("---")
    if class_name:
        result = supabase.table("attendance_records")\
            .select("*")\
            .eq("class_name", class_name)\
            .order("submitted_at", desc=True)\
            .execute()

        data = result.data or []
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df)

            # Download Button
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download CSV", csv, file_name=f"{class_name}_attendance.csv", mime="text/csv")

            # GitHub Push Button
            if st.button("📤 Push to GitHub"):
                push_csv_to_github(class_name, df)
        else:
            st.info("No attendance data found.")

def push_csv_to_github(class_name, df):
    try:
        # Generate filename and content
        filename = f"attendance_{class_name}_{datetime.now(IST).strftime('%Y%m%d_%H%M%S')}.csv"
        path = f"records/{filename}"
        content = df.to_csv(index=False)

        # GitHub push
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_user(st.secrets["GITHUB_USERNAME"]).get_repo(st.secrets["GITHUB_REPO"])
        repo.create_file(path, f"Push attendance for {class_name}", content, branch="main")

        st.success(f"✅ File pushed to GitHub: `{path}`")
    except Exception as e:
        st.error(f"❌ GitHub push failed: {e}")
