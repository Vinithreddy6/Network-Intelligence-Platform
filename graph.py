"""
graph.py - Builds the network graph model.

Node "me" is always the center, connected to every contact (edge weight
driven by relationship score). Contact-to-contact edges come from two
sources:
  1. Manual connections you record (db.connections table)
  2. Optional inference: contacts who share the same company

The result is a networkx.Graph that pages/5_Network_Graph.py renders
with Plotly.
"""

import networkx as nx
import scoring

ME_NODE = "__me__"


def build_graph(contacts, connections, db, infer_by_company=True, infer_by_tags=False):
    G = nx.Graph()
    G.add_node(ME_NODE, label="Me", kind="me", tier="Me", score=100, company="", priority="")

    scores = scoring.score_all_contacts(contacts, db)  # 2 queries total, not 2 per contact

    for c in contacts:
        s = scores[c["id"]]
        label = f"{c['first_name']} {c['last_name']}".strip()
        G.add_node(
            c["id"],
            label=label,
            kind="contact",
            tier=s["tier"],
            score=s["score"],
            company=c.get("company", ""),
            priority=c.get("priority", "Regular"),
            title=c.get("title", ""),
        )
        # edge from "me" to every contact; weight reflects relationship strength
        G.add_edge(ME_NODE, c["id"], weight=s["score"], kind="me-contact")

    # manual connections
    for conn in connections:
        a, b = conn["contact_a"], conn["contact_b"]
        if G.has_node(a) and G.has_node(b):
            G.add_edge(a, b, weight=50, kind="manual", label=conn.get("label", ""))

    # inferred: shared company
    if infer_by_company:
        by_company = {}
        for c in contacts:
            company = (c.get("company") or "").strip().lower()
            if company:
                by_company.setdefault(company, []).append(c["id"])
        for company, ids in by_company.items():
            if len(ids) > 1:
                for i in range(len(ids)):
                    for j in range(i + 1, len(ids)):
                        if not G.has_edge(ids[i], ids[j]):
                            G.add_edge(ids[i], ids[j], weight=20, kind="company")

    return G


TIER_COLORS = {
    "Me": "#7c3aed",
    "Strong": "#16a34a",
    "Warm": "#eab308",
    "Cooling": "#f97316",
    "Cold": "#dc2626",
}

# Base ring radius: closest to "Me" = strongest relationship
TIER_RADIUS = {
    "Strong": 1.3,
    "Warm": 2.4,
    "Cooling": 3.5,
    "Cold": 4.6,
}

# Small per-ring angle offset so rings don't all start at angle 0 and line
# up in a single straight spoke from the center -- purely cosmetic.
TIER_ANGLE_OFFSET = {
    "Strong": 0.0,
    "Warm": 0.35,
    "Cooling": 0.0,
    "Cold": 0.35,
}

COMFORTABLE_NODES_PER_RING = 8  # beyond this, push the ring outward so labels don't crowd


def radial_layout(G):
    """
    Places 'me' at the center, and every contact on a ring based on their
    tier: Strong = innermost ring, Cold = outermost ring. Much easier to
    read at a glance than a force-directed layout.

    Rings with a lot of contacts are pushed slightly further out so nodes
    and their name labels have room to breathe instead of overlapping.

    Returns a dict of node -> (x, y).
    """
    import math

    pos = {ME_NODE: (0.0, 0.0)}

    # group contacts by tier, in a stable order
    by_tier = {"Strong": [], "Warm": [], "Cooling": [], "Cold": []}
    for node, data in G.nodes(data=True):
        if data.get("kind") == "contact":
            by_tier.setdefault(data["tier"], []).append(node)

    for tier, nodes in by_tier.items():
        n = len(nodes)
        if n == 0:
            continue
        base_radius = TIER_RADIUS.get(tier, 4.6)
        # widen the ring a bit if it's crowded, so labels don't collide
        crowding_extra = max(0, n - COMFORTABLE_NODES_PER_RING) * 0.12
        radius = base_radius + crowding_extra
        offset = TIER_ANGLE_OFFSET.get(tier, 0.0)
        for i, node in enumerate(nodes):
            angle = offset + (2 * math.pi * i / n)
            pos[node] = (radius * math.cos(angle), radius * math.sin(angle))

    return pos
