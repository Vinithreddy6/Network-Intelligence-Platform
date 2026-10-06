import streamlit as st
import db
import scoring
import style

st.set_page_config(page_title="Contacts", page_icon="👥", layout="wide")
style.inject_css()
st.title("👥 Contacts")

tab_browse, tab_add = st.tabs(["Browse & Edit", "Add New Contact"])

with tab_browse:
    contacts = db.get_all_contacts()
    if not contacts:
        st.info("No contacts yet.")
    else:
        search = st.text_input("Search by name or company")
        filtered = contacts
        if search:
            q = search.lower()
            filtered = [
                c for c in contacts
                if q in f"{c['first_name']} {c['last_name']}".lower()
                or q in (c["company"] or "").lower()
            ]

        scores = scoring.score_all_contacts(filtered, db)  # 2 queries total, not 2 per contact
        for c in filtered:
            s = scores[c["id"]]
            emoji = style.priority_emoji(c["priority"])
            with st.expander(f"{emoji} {c['first_name']} {c['last_name']} — {c['company'] or 'No company'}"):
                st.markdown(style.tier_badge_html(s["tier"], s["score"]), unsafe_allow_html=True)
                st.write("")
                col1, col2 = st.columns(2)
                with col1:
                    first = st.text_input("First name", c["first_name"], key=f"fn_{c['id']}")
                    last = st.text_input("Last name", c["last_name"], key=f"ln_{c['id']}")
                    email = st.text_input("Email", c["email"], key=f"em_{c['id']}")
                    company = st.text_input("Company", c["company"], key=f"co_{c['id']}")
                with col2:
                    title = st.text_input("Title", c["title"], key=f"ti_{c['id']}")
                    linkedin = st.text_input("LinkedIn URL", c["linkedin_url"], key=f"li_{c['id']}")
                    priority = st.selectbox(
                        "Priority", ["Key", "Regular", "Casual"],
                        index=["Key", "Regular", "Casual"].index(c["priority"]) if c["priority"] in ["Key", "Regular", "Casual"] else 1,
                        key=f"pr_{c['id']}",
                    )
                    tags = st.text_input("Tags (comma-separated)", c["tags"], key=f"tg_{c['id']}")
                notes = st.text_area("Notes", c["notes"], key=f"no_{c['id']}")

                bcol1, bcol2 = st.columns(2)
                if bcol1.button("Save changes", key=f"save_{c['id']}"):
                    db.update_contact(
                        c["id"], first_name=first, last_name=last, email=email,
                        company=company, title=title, linkedin_url=linkedin,
                        priority=priority, tags=tags, notes=notes,
                    )
                    st.success("Saved.")
                    st.rerun()
                if bcol2.button("Delete contact", key=f"del_{c['id']}"):
                    db.delete_contact(c["id"])
                    st.warning("Deleted.")
                    st.rerun()

                st.markdown("**Interaction history**")
                history = db.get_interactions(c["id"])
                if history:
                    for h in history:
                        st.write(f"- `{h['date']}` **{h['type']}** — {h['notes']}")
                else:
                    st.caption("No interactions logged yet.")

with tab_add:
    with st.form("add_contact_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            first = st.text_input("First name *")
            last = st.text_input("Last name")
            email = st.text_input("Email")
            company = st.text_input("Company")
        with col2:
            title = st.text_input("Title")
            linkedin = st.text_input("LinkedIn URL")
            priority = st.selectbox("Priority", ["Key", "Regular", "Casual"], index=1)
            tags = st.text_input("Tags (comma-separated)")
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Add contact")
        if submitted:
            if not first.strip():
                st.error("First name is required.")
            else:
                db.add_contact(
                    first_name=first, last_name=last, email=email, company=company,
                    title=title, linkedin_url=linkedin, priority=priority,
                    tags=tags, notes=notes,
                )
                st.success(f"Added {first} {last}.")
