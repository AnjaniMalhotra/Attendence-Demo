# ---------- ✅ admin.py (Supabase + Proxy-Proof + Pivot View) ----------

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

# --- Supabase Credentials ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Admin Credentials ---
ADMIN_USERNAME = st.secrets["ADMIN_USERNAME"]
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]

# --- Show Admin Panel ---
def show_admin_panel():
    st.header("🧑‍🏫 Admin Panel")

    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                st.success("Logged in as Admin")
                st.rerun()
            else:
                st.error("Invalid credentials")
        return

    # Create or Delete Classrooms
    st.subheader("📂 Manage Classrooms")
    class_name = st.text_input("Enter New Classroom Name")
    if st.button("Create Classroom"):
        table_name = f"attendance_{class_name.replace(' ', '_')}"
        try:
            # Insert to classroom settings
            supabase.table("classroom_settings").insert({
                "class_name": class_name,
                "is_open": False,
                "code": "",
                "limit": 1
            }).execute()

            # Create attendance table using Supabase RPC (must be defined in SQL)
            supabase.rpc("create_attendance_table", {"table_name": table_name}).execute()

            st.success(f"Classroom '{class_name}' created with table '{table_name}'")
        except Exception as e:
            st.error(f"Failed to create: {e}")
        st.rerun()

    # View Existing Classrooms
    class_data = supabase.table("classroom_settings").select("*").execute()
    if not class_data.data:
        st.warning("No classrooms available.")
        return

    class_names = [cls["class_name"] for cls in class_data.data]
    selected_class = st.selectbox("Select Classroom", class_names)

    # Open/Close Attendance
    is_open = next((cls["is_open"] for cls in class_data.data if cls["class_name"] == selected_class), False)
    st.markdown(f"**Attendance for '{selected_class}' is currently:** {'🟢 OPEN' if is_open else '🔴 CLOSED'}")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Open Attendance"):
            supabase.table("classroom_settings").update({"is_open": True}).eq("class_name", selected_class).execute()
            st.success("Attendance opened")
            st.rerun()
    with col2:
        if st.button("Close Attendance"):
            supabase.table("classroom_settings").update({"is_open": False}).eq("class_name", selected_class).execute()
            st.success("Attendance closed")
            st.rerun()

    # Update Code and Limit
    selected_row = next((cls for cls in class_data.data if cls["class_name"] == selected_class), {})
    st.markdown("### 🔐 Code and Limit")
    code = st.text_input("Attendance Code", value=selected_row.get("code", ""))
    limit = st.number_input("Limit per day", min_value=1, value=selected_row.get("limit", 1))
    if st.button("Update Code & Limit"):
        supabase.table("classroom_settings").update({"code": code, "limit": limit}).eq("class_name", selected_class).execute()
        st.success("Updated")

    # Attendance Records (Pivot View)
    st.markdown("### 📊 Attendance Records (Pivot View)")
    table_name = f"attendance_{selected_class.replace(' ', '_')}"
    try:
        records = supabase.table(table_name).select("*").execute().data
        if not records:
            st.info("No attendance marked yet.")
            return

        df = pd.DataFrame(records)
        pivot_df = df.pivot_table(index=["roll_number", "name"], columns="date", aggfunc="size", fill_value=0)
        pivot_df = pivot_df.replace(1, "✔️").replace(0, "")
        pivot_df = pivot_df.reset_index()

        st.dataframe(pivot_df)

        # CSV download
        csv = pivot_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", csv, file_name=f"{selected_class}_attendance.csv", mime="text/csv")

    except Exception as e:
        st.error(f"Error loading attendance: {e}")
