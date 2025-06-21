import streamlit as st
from datetime import datetime
import pandas as pd
import os
import pytz
from supabase import create_client
from github import Github
from dotenv import load_dotenv

# Load secrets
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_REPO = os.getenv("GITHUB_REPO")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# Setup clients
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
gh = Github(GITHUB_TOKEN)
repo = gh.get_user(GITHUB_USERNAME).get_repo(GITHUB_REPO)

# Timezone IST
IST = pytz.timezone("Asia/Kolkata")
def current_ist_date():
    return datetime.now(IST).strftime("%Y-%m-%d")

def show_admin_panel():
    st.title("🧑‍🏫 Admin Panel")

    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        username = st.text_input("Username", key="admin_user")
        password = st.text_input("Password", type="password", key="admin_pass")
        if st.button("Login", key="admin_login_btn"):
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("Invalid credentials.")
        return

    if st.sidebar.button("🚪 Logout"):
        st.session_state.admin_logged_in = False
        st.rerun()

    st.subheader("📂 Manage Classrooms")

    class_input = st.text_input("Create New Class", key="new_class")
    if st.button("➕ Add Class"):
        if class_input.strip():
            existing = supabase.table("classroom_settings").select("*").eq("class_name", class_input).execute().data
            if existing:
                st.warning("⚠️ Class already exists.")
            else:
                supabase.table("classroom_settings").insert({
                    "class_name": class_input,
                    "code": "1234",
                    "daily_limit": 10,
                    "is_open": False
                }).execute()
                st.success(f"✅ Class '{class_input}' added.")
                st.rerun()

    # Load all classes
    classes = supabase.table("classroom_settings").select("*").execute().data
    if not classes:
        st.warning("No classes created yet.")
        return

    selected_class = st.selectbox("Select a Class", [c["class_name"] for c in classes], key="select_class")
    selected_config = next(c for c in classes if c["class_name"] == selected_class)

    other_open_classes = [c["class_name"] for c in classes if c["is_open"] and c["class_name"] != selected_class]

    st.subheader(f"🕹️ Attendance Control: `{selected_class}`")
    st.info(f"Status: **{'OPEN' if selected_config['is_open'] else 'CLOSED'}**")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("✅ Open Attendance"):
            if other_open_classes:
                st.warning(f"Close other open classes first: {', '.join(other_open_classes)}")
            else:
                supabase.table("classroom_settings").update({"is_open": True}).eq("class_name", selected_class).execute()
                st.success("Attendance portal opened.")
                st.rerun()
    with col2:
        if st.button("❌ Close Attendance"):
            supabase.table("classroom_settings").update({"is_open": False}).eq("class_name", selected_class).execute()
            st.success("Attendance portal closed.")
            st.rerun()
    with col3:
        st.markdown("### 🗑️ Permanently Delete Class")
        st.warning("⚠️ This will delete all attendance and student data for this class permanently.")
        confirm = st.text_input("Type `DELETE` to confirm", key="delete_confirm")

        if st.button("❌ Delete Class Permanently"):
            if confirm.strip() == "DELETE":
                supabase.table("attendance").delete().eq("class_name", selected_class).execute()
                supabase.table("roll_map").delete().eq("class_name", selected_class).execute()
                supabase.table("classroom_settings").delete().eq("class_name", selected_class).execute()
                st.success(f"✅ Classroom '{selected_class}' and all its records have been permanently deleted.")
                st.rerun()
            else:
                st.warning("⚠️ Please type `DELETE` exactly to confirm deletion.")

    # Update code & limit
    st.markdown("### 🔐 Update Attendance Code & Limit")
    new_code = st.text_input("Code", value=selected_config["code"], key="update_code")
    new_limit = st.number_input("Daily Limit", min_value=1, value=selected_config["daily_limit"], step=1, key="update_limit")
    if st.button("💾 Update Settings"):
        supabase.table("classroom_settings").update({
            "code": new_code,
            "daily_limit": new_limit
        }).eq("class_name", selected_class).execute()
        st.success("Updated successfully.")
        st.rerun()

    # Matrix Attendance View
    st.markdown("### 🧾 Attendance Sheet (Matrix View)")

    records = supabase.table("attendance").select("*") \
        .eq("class_name", selected_class).order("date", desc=True).execute().data

    if not records:
        st.info("No attendance records found.")
    else:
        df_matrix = pd.DataFrame(records)
        df_matrix["status"] = "✅"
        pivot_df = df_matrix.pivot_table(
            index=["roll_number", "name"],
            columns="date",
            values="status",
            aggfunc="first",
            fill_value="❌"
        ).reset_index()

        pivot_df.columns.name = None
        st.dataframe(pivot_df, use_container_width=True)

        # Download locally
        csv = pivot_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download CSV",
            data=csv,
            file_name=f"{selected_class}_attendance_matrix.csv",
            mime='text/csv'
        )

        # Push to GitHub
        if st.button("🚀 Push Matrix to GitHub"):
            filename = f"attendance_matrix_{selected_class}_{datetime.now(IST).strftime('%Y%m%d_%H%M%S')}.csv"
            content = pivot_df.to_csv(index=False)
            repo_path = f"records/{filename}"
            try:
                repo.create_file(repo_path, f"Add matrix attendance for {selected_class}", content, branch="main")
                st.success(f"✅ Matrix file pushed to GitHub: {repo_path}")
            except Exception as e:
                st.warning(f"⚠️ GitHub push failed: {e}")
