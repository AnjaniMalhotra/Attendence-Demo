# -------------------- ✅ admin.py --------------------

import streamlit as st
from datetime import datetime
import pandas as pd
import os
import pytz
from supabase import create_client
from github import Github
from dotenv import load_dotenv
from analytics import show_analytics_panel  # 📊 Import analytics

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

IST = pytz.timezone("Asia/Kolkata")
def current_ist_date():
    return datetime.now(IST).strftime("%Y-%m-%d")

def show_admin_panel():
    st.title("🧑\u200d🏫 Admin Panel")

    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        with st.form("admin_login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("🔐 Login"):
                if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                    st.session_state.admin_logged_in = True
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials.")
        return

    with st.sidebar:
        st.markdown("## ➕ Create Class")
        class_input = st.text_input("New Class Name")
        if st.button("➕ Add Class"):
            if class_input.strip():
                exists = supabase.table("classroom_settings").select("*").eq("class_name", class_input).execute().data
                if exists:
                    st.warning("⚠️ Class already exists.")
                else:
                    supabase.table("classroom_settings").insert({
                        "class_name": class_input,
                        "code": "1234",
                        "daily_limit": 10,
                        "is_open": False
                    }).execute()
                    st.success(f"✅ Class '{class_input}' created.")
                    st.rerun()

        if st.button("🚪 Logout"):
            st.session_state.admin_logged_in = False
            st.rerun()

    st.subheader("🏷️ Select and Manage Class")
    classes = supabase.table("classroom_settings").select("*").execute().data
    if not classes:
        st.warning("No classes available.")
        return

    selected_class = st.selectbox("📚 Select a Class", [c["class_name"] for c in classes])
    config = next(c for c in classes if c["class_name"] == selected_class)

    st.markdown(f"**Current Code:** `{config['code']}`")
    st.markdown(f"**Current Limit:** `{config['daily_limit']}`")

    st.subheader("🛠️ Attendance Controls")
    is_open = config["is_open"]
    other_open = [c["class_name"] for c in classes if c["is_open"] and c["class_name"] != selected_class]
    st.info(f"Status: **{'OPEN' if is_open else 'CLOSED'}**")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Open Attendance"):
            if other_open:
                st.warning(f"Close other classes first: {', '.join(other_open)}")
            else:
                supabase.table("classroom_settings").update({"is_open": True}).eq("class_name", selected_class).execute()
                st.rerun()
    with col2:
        if st.button("❌ Close Attendance"):
            supabase.table("classroom_settings").update({"is_open": False}).eq("class_name", selected_class).execute()
            st.rerun()

    with st.expander("🔄 Update Code & Limit"):
        new_code = st.text_input("New Code", value=config["code"])
        new_limit = st.number_input("New Limit", min_value=1, value=config["daily_limit"], step=1)
        if st.button("💾 Save Settings"):
            supabase.table("classroom_settings").update({"code": new_code, "daily_limit": new_limit}).eq("class_name", selected_class).execute()
            st.success("✅ Settings updated.")
            st.rerun()

    st.subheader("📊 Attendance Matrix View")
    records = supabase.table("attendance").select("*").eq("class_name", selected_class).order("date", desc=True).execute().data

    if records:
        df = pd.DataFrame(records)
        df["status"] = "P"
        pivot_df = df.pivot_table(index=["roll_number", "name"], columns="date", values="status", aggfunc="first", fill_value="A").reset_index()
        pivot_df["roll_number"] = pivot_df["roll_number"].astype(int)
        pivot_df = pivot_df.sort_values("roll_number")

        def highlight(val):
            return "background-color:#d4edda;color:green" if val == "P" else "background-color:#f8d7da;color:red"

        styled = pivot_df.style.applymap(highlight, subset=pivot_df.columns[2:])
        st.dataframe(styled, use_container_width=True)

        st.download_button("⬇️ Download CSV", pivot_df.to_csv(index=False).encode(), f"{selected_class}_matrix.csv", "text/csv")

        
        if st.button("🚀 Push to GitHub"):
            filename = f"records/attendance_matrix_{selected_class}_{datetime.now(IST).strftime('%Y%m%d_%H%M%S')}.csv"
            try:
                repo.create_file(filename, f"Push matrix for {selected_class}", pivot_df.to_csv(index=False), branch="main")
                st.success(f"✅ Uploaded: {filename}")
            except Exception as e:
                st.error(f"GitHub Error: {e}")
    else:
        st.info("No attendance yet.")

    # 📊 Analytics Section
     # ✅ Save a local copy to /classes/ for analytics
    local_dir = "classes"
    os.makedirs(local_dir, exist_ok=True)
    local_path = os.path.join(local_dir, f"{selected_class}_matrix.csv")
    pivot_df.to_csv(local_path, index=False)
    
    with st.expander("📈 Advanced Analytics"):
        show_analytics_panel()


    st.subheader("🗑️ Delete Class")
    st.warning("This will permanently delete the class and all attendance data.")
    if st.text_input("Type DELETE to confirm") == "DELETE":
        if st.button("❌ Delete Class"):
            supabase.table("attendance").delete().eq("class_name", selected_class).execute()
            supabase.table("roll_map").delete().eq("class_name", selected_class).execute()
            supabase.table("classroom_settings").delete().eq("class_name", selected_class).execute()
            st.success("Class deleted.")
            st.rerun()
