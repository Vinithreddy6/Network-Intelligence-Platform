import streamlit as st
from datetime import date
import db

st.set_page_config(page_title="Log Interaction", page_icon="✍️", layout="wide")
st.title("✍️ Log an Interaction")

contacts = db.get_all_contacts()
if not contacts:
    st.info("Add some contacts first (see Contacts or Import).")
    st.stop()

name_to_id = {f"{c['first_name']} {c['last_name']}".strip() + f"  ({c['company']})": c["id"] for c in contacts}

with st.form("log_form", clear_on_submit=True):
    selected_name = st.selectbox("Contact", list(name_to_id.keys()))
    itype = st.selectbox("Type", ["Call", "Email", "Meeting", "Message", "Note"])
    idate = st.date_input("Date", value=date.today())
    notes = st.text_area("Notes (what did you discuss? any follow-ups?)")
    submitted = st.form_submit_button("Log interaction")

    if submitted:
        contact_id = name_to_id[selected_name]
        db.add_interaction(contact_id, date_str=idate.isoformat(), itype=itype, notes=notes)
        st.success(f"Logged {itype.lower()} with {selected_name.split('  (')[0]} on {idate.isoformat()}.")
