import streamlit as st
import plotly.graph_objects as go
import db
import graph as graphmod
import style

st.set_page_config(page_title="Network Graph", page_icon="🕸️", layout="wide")
style.inject_css()
st.title("🕸️ Network Graph")

st.info(
    "👤 **You're the dot in the middle.** Everyone else sits on a ring around you — "
    "the **closer the ring, the stronger the relationship**. People in the outer rings "
    "are the ones you've been losing touch with. ⭐ marks your **Key** contacts.",
    icon="💡",
)

contacts = db.get_all_contacts()
if not contacts:
    st.info("Add some contacts first (see Contacts or Import).")
    st.stop()

connections = db.get_all_connections()

# --- Simple, minimal controls (advanced stuff tucked away) ---
show_company_links = st.checkbox("Show lines between people who work at the same company", value=False)

with st.expander("⚙️ More options"):
    show_labels = st.checkbox("Show name labels on the graph", value=True)
    priority_filter = st.multiselect(
        "Only show these priority levels", ["Key", "Regular", "Casual"],
        default=["Key", "Regular", "Casual"],
    )

filtered_contacts = [c for c in contacts if c["priority"] in priority_filter]
filtered_ids = {c["id"] for c in filtered_contacts}
filtered_connections = [
    conn for conn in connections
    if conn["contact_a"] in filtered_ids and conn["contact_b"] in filtered_ids
]

G = graphmod.build_graph(filtered_contacts, filtered_connections, db, infer_by_company=show_company_links)

# --- Radial layout: rings by relationship strength, with smart spacing ---
pos = graphmod.radial_layout(G)

# figure out the outer bound so our shaded rings / view box fit everything
max_radius = max(
    (abs(x) for x, y in pos.values()), default=5
)
max_radius = max(max_radius, max((abs(y) for x, y in pos.values()), default=5), 5) + 0.8

# --- Shaded concentric bands, largest first so smaller rings layer on top ---
ring_shapes = []
ring_annotations = []
tier_radii_sorted = sorted(graphmod.TIER_RADIUS.items(), key=lambda kv: kv[1], reverse=True)
for tier, radius in tier_radii_sorted:
    ring_shapes.append(dict(
        type="circle", xref="x", yref="y",
        x0=-radius, y0=-radius, x1=radius, y1=radius,
        line=dict(color=style.TIER_COLORS.get(tier, "#cbd5e1"), width=1.2, dash="dot"),
        fillcolor=style.TIER_BG.get(tier, "rgba(0,0,0,0)"),
        opacity=0.35,
        layer="below",
    ))
    ring_annotations.append(dict(
        x=0, y=radius, text=f"<b>{tier}</b>", showarrow=False,
        font=dict(size=11, color=style.TIER_COLORS.get(tier, "#94a3b8")),
        yshift=10,
    ))

# soft glow behind the "You" node
glow_shape = dict(
    type="circle", xref="x", yref="y",
    x0=-0.5, y0=-0.5, x1=0.5, y1=0.5,
    line=dict(width=0),
    fillcolor="rgba(124, 58, 237, 0.18)",
    layer="below",
)
ring_shapes.append(glow_shape)

# --- Edges ---
edge_traces = []
for kind, color, width in [
    ("me-contact", "#e2e8f0", 1),
    ("company", "#93c5fd", 1.5),
    ("manual", "#f472b6", 2.5),
]:
    edge_x, edge_y = [], []
    for u, v, data in G.edges(data=True):
        if data.get("kind") == kind and u in pos and v in pos:
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]
    if edge_x:
        edge_traces.append(go.Scatter(
            x=edge_x, y=edge_y, mode="lines",
            line=dict(width=width, color=color),
            hoverinfo="none", showlegend=False,
        ))

# --- Nodes (split into two traces so Key contacts get a star marker) ---
def node_arrays(predicate):
    xs, ys, colors, sizes, texts, labels = [], [], [], [], [], []
    for node, data in G.nodes(data=True):
        if node not in pos or not predicate(data):
            continue
        x, y = pos[node]
        xs.append(x)
        ys.append(y)
        colors.append(graphmod.TIER_COLORS.get(data["tier"], "#94a3b8"))
        if data["kind"] == "me":
            sizes.append(38)
            texts.append("You")
            labels.append("You")
        else:
            sizes.append(18 + data["score"] / 7)
            hover = (f"<b>{data['label']}</b><br>{data.get('title', '')}<br>"
                     f"{data.get('company', '')}<br>Score: {data['score']} ({data['tier']})")
            texts.append(hover)
            labels.append(data["label"] if show_labels else "")
    return xs, ys, colors, sizes, texts, labels

traces = []

# "Me" node
xs, ys, colors, sizes, texts, labels = node_arrays(lambda d: d["kind"] == "me")
if xs:
    traces.append(go.Scatter(
        x=xs, y=ys, mode="markers+text",
        text=labels, textposition="top center", textfont=dict(size=12, color="#4c1d95"),
        hovertext=texts, hoverinfo="text",
        marker=dict(size=sizes, color=colors, line=dict(width=3, color="white"), symbol="circle"),
        showlegend=False,
    ))

# Key contacts -> star marker
xs, ys, colors, sizes, texts, labels = node_arrays(lambda d: d["kind"] == "contact" and d.get("priority") == "Key")
if xs:
    traces.append(go.Scatter(
        x=xs, y=ys, mode="markers+text" if show_labels else "markers",
        text=labels, textposition="top center", textfont=dict(size=10),
        hovertext=texts, hoverinfo="text",
        marker=dict(size=sizes, color=colors, line=dict(width=2, color="white"), symbol="star"),
        showlegend=False,
    ))

# Everyone else -> plain circle marker
xs, ys, colors, sizes, texts, labels = node_arrays(
    lambda d: d["kind"] == "contact" and d.get("priority") != "Key"
)
if xs:
    traces.append(go.Scatter(
        x=xs, y=ys, mode="markers+text" if show_labels else "markers",
        text=labels, textposition="top center", textfont=dict(size=10),
        hovertext=texts, hoverinfo="text",
        marker=dict(size=sizes, color=colors, line=dict(width=2, color="white"), symbol="circle"),
        showlegend=False,
    ))

fig = go.Figure(data=edge_traces + traces)
fig.update_layout(
    shapes=ring_shapes,
    annotations=ring_annotations,
    showlegend=False,
    hovermode="closest",
    margin=dict(l=10, r=10, t=10, b=10),
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, scaleanchor="y",
               range=[-max_radius, max_radius]),
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
               range=[-max_radius, max_radius]),
    height=650,
    plot_bgcolor="white",
)

st.plotly_chart(fig, use_container_width=True)

st.markdown(
    "🟣 **You** &nbsp;·&nbsp; 🟢 **Strong** &nbsp;·&nbsp; 🟡 **Warm** &nbsp;·&nbsp; "
    "🟠 **Cooling** &nbsp;·&nbsp; 🔴 **Cold** &nbsp;·&nbsp; ⭐ **Key contact**"
)
st.caption("Hover over any dot to see that person's name, company, and score.")

st.divider()

with st.expander("➕ Record that two contacts know each other (optional)"):
    st.caption("e.g. 'Jane introduced me to Sam', or 'they're colleagues'. This adds a pink line between them.")
    name_to_id = {f"{c['first_name']} {c['last_name']}".strip(): c["id"] for c in contacts}
    names = list(name_to_id.keys())

    with st.form("add_connection_form", clear_on_submit=True):
        c1, c2, c3 = st.columns([2, 2, 3])
        person_a = c1.selectbox("Contact A", names, key="conn_a")
        person_b = c2.selectbox("Contact B", names, key="conn_b")
        label = c3.text_input("Label (optional)", placeholder="e.g. introduced me")
        submitted = st.form_submit_button("Add connection")
        if submitted:
            if person_a == person_b:
                st.error("Pick two different contacts.")
            else:
                result = db.add_connection(name_to_id[person_a], name_to_id[person_b], label=label)
                if result:
                    st.success(f"Connected {person_a} ↔ {person_b}.")
                    st.rerun()
                else:
                    st.info("That connection already exists.")

    if connections:
        id_to_name = {c["id"]: f"{c['first_name']} {c['last_name']}".strip() for c in contacts}
        for conn in connections:
            a_name = id_to_name.get(conn["contact_a"], "?")
            b_name = id_to_name.get(conn["contact_b"], "?")
            colA, colB = st.columns([5, 1])
            colA.write(f"**{a_name}** ↔ **{b_name}**" + (f" — _{conn['label']}_" if conn["label"] else ""))
            if colB.button("Remove", key=f"rmconn_{conn['id']}"):
                db.delete_connection(conn["id"])
                st.rerun()
