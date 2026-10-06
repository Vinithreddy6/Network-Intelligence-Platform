import streamlit as st
import db
import importer

st.set_page_config(page_title="Import", page_icon="📥", layout="wide")
st.title("📥 Import Contacts")

st.markdown(
    """
Upload a CSV file. This works directly with **LinkedIn's "Connections.csv"**
export (Settings → Data privacy → Get a copy of your data → Connections),
or any generic CSV of contacts.
"""
)

uploaded = st.file_uploader("Choose a CSV file", type=["csv"])

if uploaded:
    raw_text = uploaded.read().decode("utf-8", errors="replace")
    fieldnames, dict_rows, suggested = importer.sniff_csv(raw_text)

    st.success(f"Found {len(dict_rows)} rows and {len(fieldnames)} columns.")
    st.caption("Detected columns: " + ", ".join(fieldnames))

    st.subheader("Map columns")
    st.caption("We've guessed a mapping below — adjust anything that looks wrong.")

    mapping = {}
    options = ["(none)"] + fieldnames
    field_labels = {
        "first_name": "First name *",
        "last_name": "Last name",
        "email": "Email",
        "company": "Company",
        "title": "Title / Position",
        "linkedin_url": "LinkedIn URL",
        "connected_on": "Connected on",
    }
    cols = st.columns(2)
    for i, (our_field, label) in enumerate(field_labels.items()):
        default = suggested.get(our_field) or "(none)"
        default_idx = options.index(default) if default in options else 0
        chosen = cols[i % 2].selectbox(label, options, index=default_idx, key=f"map_{our_field}")
        mapping[our_field] = None if chosen == "(none)" else chosen

    default_priority = st.selectbox(
        "Default priority for imported contacts", ["Key", "Regular", "Casual"], index=1
    )

    if st.button("Preview import"):
        contacts = importer.rows_to_contacts(dict_rows, mapping)
        st.session_state["_import_preview"] = contacts

    if "_import_preview" in st.session_state:
        contacts = st.session_state["_import_preview"]
        st.subheader(f"Preview ({len(contacts)} contacts to import)")
        st.dataframe(contacts[:20], use_container_width=True)
        if len(contacts) > 20:
            st.caption(f"... and {len(contacts) - 20} more")

        skip_dupes = st.checkbox("Skip contacts that already exist (match by email / LinkedIn URL / name)", value=True)

        if st.button("Confirm import", type="primary"):
            added, skipped = 0, 0
            for c in contacts:
                if skip_dupes:
                    existing = db.contact_exists(
                        email=c.get("email", ""),
                        linkedin_url=c.get("linkedin_url", ""),
                        first_name=c.get("first_name", ""),
                        last_name=c.get("last_name", ""),
                    )
                    if existing:
                        skipped += 1
                        continue
                db.add_contact(
                    first_name=c.get("first_name", ""),
                    last_name=c.get("last_name", ""),
                    email=c.get("email", ""),
                    company=c.get("company", ""),
                    title=c.get("title", ""),
                    linkedin_url=c.get("linkedin_url", ""),
                    connected_on=c.get("connected_on", ""),
                    priority=default_priority,
                )
                added += 1
            st.success(f"Imported {added} contacts. Skipped {skipped} duplicates.")
            del st.session_state["_import_preview"]
