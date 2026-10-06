"""
scoring.py - Relationship strength scoring.

Score (0-100) blends two signals:
  1. Recency  - exponential decay since last interaction. Decay speed
                depends on the contact's priority tier: Key contacts are
                expected to be touched more often, so their score decays
                faster if neglected.
  2. Frequency - how many interactions happened in the last 180 days,
                 capped and normalized.

Final score = 0.65 * recency + 0.35 * frequency

Tiers (for display and reminders):
  Strong   80-100
  Warm     55-79
  Cooling  30-54
  Cold     0-29
"""

import math
from datetime import date, datetime, timedelta

# Half-life in days: time for the recency score to drop to 50, per priority.
HALF_LIFE_DAYS = {
    "Key": 21,
    "Regular": 60,
    "Casual": 150,
}

FREQUENCY_WINDOW_DAYS = 180
FREQUENCY_CAP = 5  # interactions in the window that maxes out the frequency score

RECENCY_WEIGHT = 0.65
FREQUENCY_WEIGHT = 0.35

TIERS = [
    (80, "Strong"),
    (55, "Warm"),
    (30, "Cooling"),
    (0, "Cold"),
]


def _days_since(date_str):
    if not date_str:
        return None
    d = datetime.fromisoformat(date_str).date()
    return (date.today() - d).days


def recency_score(last_interaction_date_str, priority="Regular"):
    days = _days_since(last_interaction_date_str)
    if days is None:
        return 0.0  # never contacted
    half_life = HALF_LIFE_DAYS.get(priority, HALF_LIFE_DAYS["Regular"])
    return 100.0 * math.exp(-math.log(2) * days / half_life)


def frequency_score(interaction_count_in_window):
    return 100.0 * min(interaction_count_in_window, FREQUENCY_CAP) / FREQUENCY_CAP


def combined_score(last_interaction_date_str, interaction_count_in_window, priority="Regular"):
    r = recency_score(last_interaction_date_str, priority)
    f = frequency_score(interaction_count_in_window)
    score = RECENCY_WEIGHT * r + FREQUENCY_WEIGHT * f
    return round(score, 1)


def tier_for_score(score):
    for threshold, label in TIERS:
        if score >= threshold:
            return label
    return "Cold"


def score_contact(contact, db):
    """
    Scores a SINGLE contact. Convenient for one-off lookups, but makes
    2 database round-trips -- calling this in a loop over many contacts
    (e.g. a whole page) is slow. For a page that scores every contact,
    use score_all_contacts() instead, which does it in 2 queries total.

    contact: dict with at least 'id' and 'priority'
    db: the db module (passed in to avoid a circular import at module load)
    Returns dict with score, tier, days_since_contact, last_date.
    """
    last_date = db.last_interaction_date(contact["id"])
    window_start = (date.today() - timedelta(days=FREQUENCY_WINDOW_DAYS)).isoformat()
    count = db.interaction_count_since(contact["id"], window_start)
    priority = contact.get("priority", "Regular")

    score = combined_score(last_date, count, priority)
    return {
        "score": score,
        "tier": tier_for_score(score),
        "days_since_contact": _days_since(last_date),
        "last_date": last_date,
        "interactions_180d": count,
    }


def score_all_contacts(contacts, db):
    """
    Scores a whole list of contacts efficiently: 2 database queries total,
    no matter how many contacts there are, instead of 2 queries PER contact.
    This is what the Dashboard, Contacts, and Network Graph pages should use.

    Returns dict: contact_id -> same shape as score_contact()'s return value.
    """
    last_dates, counts = db.get_interaction_stats_bulk(window_days=FREQUENCY_WINDOW_DAYS)

    results = {}
    for c in contacts:
        cid = c["id"]
        last_date = last_dates.get(cid)
        count = counts.get(cid, 0)
        priority = c.get("priority", "Regular")

        score = combined_score(last_date, count, priority)
        results[cid] = {
            "score": score,
            "tier": tier_for_score(score),
            "days_since_contact": _days_since(last_date),
            "last_date": last_date,
            "interactions_180d": count,
        }
    return results
