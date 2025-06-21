# ---------- ✅ admin.py (Supabase + Proxy-Proof + Pivot View + Full Features) ----------

import streamlit as st
import pandas as pd
import pytz
from datetime import datetime
from supabase import create_client
import os
from github import Github

# --- Timezone Setup ---
IST = pytz.timezone('Asia/Kolkata')
def current_ist_date():
    return datetime.now(IST).strftime("%Y-%m-%d")

# --- Supabase Setup ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Admin + GitHub Credentials ---
ADMIN_USERNAME = st.secrets["ADMIN_USERNAME"]
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
GITHUB_USERNAME = st.secrets["GITHUB_USERNAME"]
GITHUB_REPO = st.secrets["GITHUB_REPO"]

# --- GitHub Push ---
def push_to_github(df, class_name):
    g = Github(GITHUB_TOKEN)
    repo = g.get_user(GITHUB_USERNAME).get_repo(GITHUB_REPO)
    file_name = f"attendance_{class_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    content = df.to_csv(index=False)
    try:
        repo.create_file(f"records/{file_name}", f"Upload attendance for {class_name}", content, branch="main")
        st.success("✅ File pushed to GitHub.")
    except Exception as e:
        st.warning(f"⚠️ GitHub push failed: {e}")

# --- Admin Panel UI ---
def show_admin_panel():
    st.header("🧑‍🏫 Admin Panel")

    # --- Login ---
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                st.success("✅ Logged in as Admin")
                st.rerun()
            else:
                st.error("Invalid credentials")
        return

    # --- Create New Class ---
    st.subheader("📂 Create New Classroom")
    new_class = st.text_input("Class Name")
    if st.button("Create Classroom"):
        if new_class.strip():
            try:
                table_name = f"attendance_{new_class.replace(' ', '_')}"
                
                # 1. Add to classroom_settings
                supabase.table("classroom_settings").insert({
                    "class_name": new_class,
                    "is_open": False,
                    "code": "",
                    "limit": 1
                }).execute()
                
                # 2. Create attendance table using Supabase RPC
                supabase.rpc("create_attendance_table", {"table_name": table_name}).execute()
                
                st.success(f"✅ Classroom '{new_class}' created and attendance table initialized.")
                st.rerun()
            except Exception as e:
                st.error(f"Error creating classroom: {e}")

    # --- View & Manage Classrooms ---
    class_data = supabase.table("classroom_settings").select("*").execute().data
    if not class_data:
        st.warning("No classrooms available.")
        return

    class_names = [item["class_name"] for item in class_data]
    selected_class = st.selectbox("Select Classroom", class_names)
    table_name = f"attendance_{selected_class.replace(' ', '_')}"
    class_info = next((x for x in class_data if x["class_name"] == selected_class), {})

    # --- Open/Close Portal ---
    st.markdown(f"### 🔄 Attendance Portal: {'🟢 OPEN' if class_info.get('is_open') else '🔴 CLOSED'}")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Open Attendance"):
            supabase.table("classroom_settings").update({"is_open": True}).eq("class_name", selected_class).execute()
            st.rerun()
    with col2:
        if st.button("Close Attendance"):
            supabase.table("classroom_settings").update({"is_open": False}).eq("class_name", selected_class).execute()
            st.rerun()

    # --- Code & Limit ---
    st.markdown("### 🔐 Attendance Code & Limit")
    code = st.text_input("Code", value=class_info.get("code", ""))
    limit = st.number_input("Limit", value=class_info.get("limit", 1), min_value=1)
    if st.button("Update Code & Limit"):
        supabase.table("classroom_settings").update({"code": code, "limit": limit}).eq("class_name", selected_class).execute()
        st.success("✅ Updated successfully.")

    # --- Delete Class ---
    if st.button("🗑️ Delete Class"):
        try:
            supabase.table("classroom_settings").delete().eq("class_name", selected_class).execute()
            supabase.rpc("drop_attendance_table", {"table_name": table_name}).execute()
            st.success("Classroom deleted")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to delete class: {e}")

    # --- View Attendance (Pivot Table) ---
    st.markdown("### 📊 Attendance Records")
    try:
        records = supabase.table(table_name).select("*").execute().data
        if not records:
            st.info("No attendance yet.")
            return

        df = pd.DataFrame(records)
        df = df[["roll_number", "name", "date"]]

        # Pivot: Rows = Roll & Name, Columns = Dates
        pivot_df = df.pivot_table(index=["roll_number", "name"], columns="date", aggfunc="size", fill_value=0)
        pivot_df = pivot_df.replace(1, "✔️").replace(0, "")
        pivot_df = pivot_df.reset_index()

        st.dataframe(pivot_df)

        # CSV Download
        csv = pivot_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", csv, file_name=f"{selected_class}_pivot_attendance.csv", mime="text/csv")

        # GitHub Push
        if st.button("📤 Push to GitHub"):
            push_to_github(pivot_df, selected_class)

    except Exception as e:
        st.error(f"Error retrieving attendance: {e}")
