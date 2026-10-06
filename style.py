"""
style.py - Shared CSS and small visual helpers used across pages,
to make the app feel less like a default Streamlit table dump.
"""

import streamlit as st

TIER_COLORS = {
    "Strong": "#16a34a",
    "Warm": "#eab308",
    "Cooling": "#f97316",
    "Cold": "#dc2626",
    "Me": "#7c3aed",
}

TIER_BG = {
    "Strong": "#dcfce7",
    "Warm": "#fef9c3",
    "Cooling": "#ffedd5",
    "Cold": "#fee2e2",
}


def inject_css():
    st.markdown(
        """
        <style>
        /* Card-style metric containers */
        div[data-testid="stMetric"] {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 14px 16px;
        }
        /* Expander headers a bit bolder */
        .streamlit-expanderHeader {
            font-weight: 600;
        }
        /* Tighter top padding */
        .block-container {
            padding-top: 2rem;
        }
        .tier-badge {
            display: inline-block;
            padding: 2px 10px;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 600;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def tier_badge_html(tier, score=None):
    color = TIER_COLORS.get(tier, "#64748b")
    bg = TIER_BG.get(tier, "#f1f5f9")
    text = f"{tier}" if score is None else f"{tier} · {score}"
    return f'<span class="tier-badge" style="color:{color};background:{bg};">{text}</span>'


def priority_emoji(priority):
    return {"Key": "⭐", "Regular": "🔹", "Casual": "◽"}.get(priority, "🔹")
