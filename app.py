import streamlit as st
import db
import style

st.set_page_config(
    page_title="Network Intelligence",
    page_icon="🕸️",
    layout="wide",
)

db.init_db()
style.inject_css()

st.title("🕸️ Network Intelligence Platform")
st.caption("Know who to reach out to, before you lose touch.")

contacts = db.get_all_contacts()
interactions = db.get_all_interactions()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total contacts", len(contacts))
col2.metric("Logged interactions", len(interactions))
key_contacts = sum(1 for c in contacts if c.get("priority") == "Key")
col3.metric("⭐ Key contacts", key_contacts)
companies = len({c["company"].strip().lower() for c in contacts if c.get("company")})
col4.metric("Companies represented", companies)

st.divider()

st.markdown(
    """
### Where to go next
| Page | What it's for |
|---|---|
| 📥 **Import** | Bring in contacts from a CSV or LinkedIn export |
| 👥 **Contacts** | Browse, search, edit your network |
| ✍️ **Log Interaction** | Record a call, email, meeting, or note |
| 📊 **Dashboard** | See relationship scores and who to reach out to |
| 🕸️ **Network Graph** | Visualize your whole network, centered on you |
"""
)

if not contacts:
    st.info("👋 New here? Start with **Import** in the sidebar to load your contacts.")
