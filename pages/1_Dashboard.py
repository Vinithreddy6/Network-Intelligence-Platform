import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import db
import scoring
import style

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
style.inject_css()
st.title("📊 Dashboard")

contacts = db.get_all_contacts()

if not contacts:
    st.info("No contacts yet. Head to the **Import** page to add some.")
    st.stop()

scores = scoring.score_all_contacts(contacts, db)  # 2 queries total, not 2 per contact

rows = []
for c in contacts:
    s = scores[c["id"]]
    rows.append({
        "id": c["id"],
        "Name": f"{c['first_name']} {c['last_name']}".strip(),
        "Company": c["company"],
        "Priority": c["priority"],
        "Score": s["score"],
        "Tier": s["tier"],
        "Days since contact": s["days_since_contact"] if s["days_since_contact"] is not None else None,
        "Last touch": s["last_date"] or "Never",
    })

df = pd.DataFrame(rows).sort_values("Score")

# --- Summary metrics ---
tier_counts = df["Tier"].value_counts()
cols = st.columns(4)
for col, tier in zip(cols, ["Strong", "Warm", "Cooling", "Cold"]):
    with col:
        st.markdown(
            f'<div style="text-align:center;padding:14px;border-radius:10px;'
            f'background:{style.TIER_BG.get(tier)};border:1px solid {style.TIER_COLORS.get(tier)}33;">'
            f'<div style="font-size:1.8rem;font-weight:700;color:{style.TIER_COLORS.get(tier)};">'
            f'{int(tier_counts.get(tier, 0))}</div>'
            f'<div style="font-size:0.85rem;color:#475569;">{tier} relationships</div></div>',
            unsafe_allow_html=True,
        )

st.divider()

# --- Distribution chart ---
chart_col, reminder_col = st.columns([1, 2])

with chart_col:
    st.markdown("**Relationship health**")
    tiers_order = ["Strong", "Warm", "Cooling", "Cold"]
    values = [int(tier_counts.get(t, 0)) for t in tiers_order]
    colors = [style.TIER_COLORS[t] for t in tiers_order]
    fig = go.Figure(data=[go.Pie(
        labels=tiers_order, values=values, hole=0.55,
        marker=dict(colors=colors), textinfo="label+value",
    )])
    fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=10, b=10), height=280)
    st.plotly_chart(fig, use_container_width=True)

with reminder_col:
    st.markdown("**🔔 Reach out soon**")
    needs_attention = df[df["Tier"].isin(["Cooling", "Cold"])].copy()
    priority_filter = st.multiselect(
        "Filter by priority", options=["Key", "Regular", "Casual"],
        default=["Key", "Regular", "Casual"], label_visibility="collapsed",
    )
    needs_attention = needs_attention[needs_attention["Priority"].isin(priority_filter)]

    if needs_attention.empty:
        st.success("Nothing urgent — your network is warm! 🎉")
    else:
        st.dataframe(
            needs_attention[["Name", "Company", "Priority", "Score", "Tier", "Days since contact"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Score": st.column_config.ProgressColumn(
                    "Score", min_value=0, max_value=100, format="%d"
                ),
            },
        )

st.divider()

# --- Full table with progress bars ---
st.subheader("All contacts by score")
sort_choice = st.radio("Sort by", ["Score (low to high)", "Score (high to low)", "Name"], horizontal=True)
if sort_choice == "Score (low to high)":
    df_sorted = df.sort_values("Score")
elif sort_choice == "Score (high to low)":
    df_sorted = df.sort_values("Score", ascending=False)
else:
    df_sorted = df.sort_values("Name")

st.dataframe(
    df_sorted[["Name", "Company", "Priority", "Score", "Tier", "Days since contact", "Last touch"]],
    use_container_width=True,
    hide_index=True,
    column_config={
        "Score": st.column_config.ProgressColumn(
            "Score", min_value=0, max_value=100, format="%d"
        ),
    },
)
