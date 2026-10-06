"""
importer.py - Import contacts from a CSV file, including LinkedIn's
"Connections.csv" export format.

LinkedIn's export has a few "Notes:" lines before the real header row, so
we scan for the header instead of assuming row 0. Standard LinkedIn columns:
First Name, Last Name, URL, Email Address, Company, Position, Connected On
"""

import csv
import io

LINKEDIN_HEADER_HINTS = {"First Name", "Last Name", "URL", "Email Address"}

# Maps our internal field -> list of possible source column names (case-insensitive)
FIELD_ALIASES = {
    "first_name": ["first name", "firstname", "first"],
    "last_name": ["last name", "lastname", "last"],
    "email": ["email address", "email"],
    "company": ["company", "organization"],
    "title": ["position", "title", "job title"],
    "linkedin_url": ["url", "linkedin url", "profile url"],
    "connected_on": ["connected on", "connection date"],
}


def _find_header_row(raw_text):
    """LinkedIn exports prepend note lines. Find the row that looks like a header."""
    reader = csv.reader(io.StringIO(raw_text))
    rows = list(reader)
    for i, row in enumerate(rows):
        cleaned = {c.strip() for c in row}
        if LINKEDIN_HEADER_HINTS & cleaned:
            return i, rows
    return 0, rows  # fall back: assume first row is the header


def sniff_csv(raw_text):
    """
    Returns (fieldnames, rows_as_dicts, suggested_mapping)
    suggested_mapping: dict of our field -> source column name (or None)
    """
    header_idx, rows = _find_header_row(raw_text)
    fieldnames = [f.strip() for f in rows[header_idx]]
    data_rows = rows[header_idx + 1:]

    dict_rows = []
    for r in data_rows:
        if not any(cell.strip() for cell in r):
            continue
        padded = r + [""] * (len(fieldnames) - len(r))
        dict_rows.append(dict(zip(fieldnames, padded)))

    lower_fieldnames = {f.lower(): f for f in fieldnames}
    suggested_mapping = {}
    for our_field, aliases in FIELD_ALIASES.items():
        match = None
        for alias in aliases:
            if alias in lower_fieldnames:
                match = lower_fieldnames[alias]
                break
        suggested_mapping[our_field] = match

    return fieldnames, dict_rows, suggested_mapping


def rows_to_contacts(dict_rows, mapping):
    """
    mapping: our_field -> source column name (as produced by sniff_csv, possibly edited by the user)
    Returns a list of contact dicts ready for db.add_contact(**contact)
    """
    contacts = []
    for row in dict_rows:
        contact = {}
        for our_field, source_col in mapping.items():
            value = row.get(source_col, "").strip() if source_col else ""
            contact[our_field] = value
        # Skip rows with no name at all
        if not contact.get("first_name") and not contact.get("last_name"):
            continue
        contacts.append(contact)
    return contacts
