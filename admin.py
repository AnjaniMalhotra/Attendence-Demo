# ---------- ✅ admin.py (Supabase + Pivot View + Dynamic Tables) ----------

import streamlit as st
import pandas as pd
import pytz
from datetime import datetime
from supabase import create_client
import os

# --- Timezone Setup ---
IST = pytz.timezone('Asia/Kolkata')
def current_ist_date():
    return datetime.now(IST).strftime("%Y-%m-%d")

# --- Supabase Setup ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

ADMIN_USERNAME = st.secrets["ADMIN_USERNAME"]
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]

# --- Main Admin Panel ---
def show_admin_panel():
    st.header("🧑‍🏫 Admin Panel")

    # Login
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

    # Create Class
    st.subheader("📂 Create New Classroom")
    new_class = st.text_input("Class Name")

    if st.button("Create Classroom"):
        if new_class.strip():
            try:
                class_table = f"attendance_{new_class.replace(' ', '_')}"

                # Insert into classroom_settings
                supabase.table("classroom_settings").insert({
                    "class_name": new_class,
                    "is_open": False,
                    "code": "",
                    "limit": 1
                }).execute()

                # Create table via RPC or raw SQL
                # (Assuming you've created an SQL function called `create_attendance_table`)
                supabase.rpc("create_attendance_table", {"table_name": class_table}).execute()
                st.success(f"Classroom '{new_class}' and its table were created.")
                st.rerun()
            except Exception as e:
                st.error(f"Error creating classroom: {e}")

    # Select Classroom
    settings_data = supabase.table("classroom_settings").select("*").execute().data
    if not settings_data:
        st.warning("No classes created yet.")
        return

    class_names = [item["class_name"] for item in settings_data]
    selected_class = st.selectbox("Select Class", class_names)

    table_name = f"attendance_{selected_class.replace(' ', '_')}"
    selected_row = next((x for x in settings_data if x["class_name"] == selected_class), {})

    # Attendance Status
    st.markdown(f"### 🔄 Attendance Portal: {'🟢 OPEN' if selected_row.get('is_open') else '🔴 CLOSED'}")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Open Attendance"):
            supabase.table("classroom_settings").update({"is_open": True}).eq("class_name", selected_class).execute()
            st.rerun()
    with col2:
        if st.button("Close Attendance"):
            supabase.table("classroom_settings").update({"is_open": False}).eq("class_name", selected_class).execute()
            st.rerun()

    # Code and Limit
    st.markdown("### 🔐 Attendance Code & Limit")
    code = st.text_input("Code", value=selected_row.get("code", ""))
    limit = st.number_input("Limit", value=selected_row.get("limit", 1), min_value=1)
    if st.button("Update Code & Limit"):
        supabase.table("classroom_settings").update({"code": code, "limit": limit}).eq("class_name", selected_class).execute()
        st.success("✅ Code and limit updated.")

    # Attendance Data (Pivot View)
    st.markdown("### 📊 Attendance Records")
    try:
        records = supabase.table(table_name).select("*").execute().data
        if not records:
            st.info("No attendance records yet.")
            return

        df = pd.DataFrame(records)
        df = df[["roll_number", "name", "date"]]

        pivot_df = df.pivot_table(index=["roll_number", "name"], columns="date", aggfunc="size", fill_value=0)
        pivot_df = pivot_df.replace(1, "✔️").replace(0, "")
        pivot_df = pivot_df.reset_index()

        st.dataframe(pivot_df)

        csv = pivot_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", csv, file_name=f"{selected_class}_pivot_attendance.csv", mime="text/csv")

    except Exception as e:
        st.error(f"Error retrieving attendance: {e}")
