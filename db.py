"""
db.py - MySQL storage layer for the Network Intelligence Platform.

Uses pymysql directly (no ORM). Connection settings come from environment
variables, with sensible localhost defaults:

  MYSQL_HOST      default: localhost
  MYSQL_PORT      default: 3306
  MYSQL_USER      default: root
  MYSQL_PASSWORD  default: '' (empty)
  MYSQL_DB        default: network_intel

Set them before running the app, e.g. (Mac/Linux):
  export MYSQL_PASSWORD="yourpassword"
or (Windows PowerShell):
  $env:MYSQL_PASSWORD = "yourpassword"

You must create the database once yourself before first run:
  CREATE DATABASE network_intel;
Tables are then created automatically the first time the app starts.

Three tables:
  contacts:     one row per person in your network
  interactions: one row per logged touchpoint (call, email, meeting, etc.)
  connections:  manually-recorded ties between two of your contacts
"""

import os
from contextlib import contextmanager
from datetime import date, timedelta

import pymysql
import pymysql.cursors

MYSQL_CONFIG = dict(
    host=os.environ.get("MYSQL_HOST", "localhost"),
    port=int(os.environ.get("MYSQL_PORT", "3306")),
    user=os.environ.get("MYSQL_USER", "root"),
    password=os.environ.get("MYSQL_PASSWORD", ""),
    database=os.environ.get("MYSQL_DB", "network_intel"),
    cursorclass=pymysql.cursors.DictCursor,
    autocommit=False,
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS contacts (
    id            INT PRIMARY KEY AUTO_INCREMENT,
    first_name    VARCHAR(255) NOT NULL,
    last_name     VARCHAR(255) DEFAULT '',
    email         VARCHAR(255) DEFAULT '',
    company       VARCHAR(255) DEFAULT '',
    title         VARCHAR(255) DEFAULT '',
    linkedin_url  VARCHAR(500) DEFAULT '',
    tags          VARCHAR(500) DEFAULT '',
    priority      VARCHAR(20) DEFAULT 'Regular',
    notes         TEXT,
    connected_on  VARCHAR(50) DEFAULT '',
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS interactions (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    contact_id  INT NOT NULL,
    date        VARCHAR(20) NOT NULL,
    type        VARCHAR(50) DEFAULT 'Note',
    notes       TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE,
    INDEX idx_interactions_contact (contact_id)
);
CREATE TABLE IF NOT EXISTS connections (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    contact_a   INT NOT NULL,
    contact_b   INT NOT NULL,
    label       VARCHAR(255) DEFAULT '',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contact_a) REFERENCES contacts(id) ON DELETE CASCADE,
    FOREIGN KEY (contact_b) REFERENCES contacts(id) ON DELETE CASCADE,
    UNIQUE KEY uniq_pair (contact_a, contact_b)
);
"""


@contextmanager
def get_conn():
    conn = pymysql.connect(**MYSQL_CONFIG)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            for statement in SCHEMA.strip().split(";"):
                statement = statement.strip()
                if statement:
                    cur.execute(statement)


# ---------- Contacts ----------

def add_contact(first_name, last_name="", email="", company="", title="",
                 linkedin_url="", tags="", priority="Regular", notes="",
                 connected_on=""):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO contacts
                   (first_name, last_name, email, company, title, linkedin_url,
                    tags, priority, notes, connected_on)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (first_name, last_name, email, company, title, linkedin_url,
                 tags, priority, notes, connected_on),
            )
            return cur.lastrowid


def contact_exists(email="", linkedin_url="", first_name="", last_name=""):
    with get_conn() as conn:
        with conn.cursor() as cur:
            if email:
                cur.execute(
                    "SELECT id FROM contacts WHERE email = %s AND email != ''", (email,)
                )
                row = cur.fetchone()
                if row:
                    return row["id"]
            if linkedin_url:
                cur.execute(
                    "SELECT id FROM contacts WHERE linkedin_url = %s AND linkedin_url != ''",
                    (linkedin_url,),
                )
                row = cur.fetchone()
                if row:
                    return row["id"]
            cur.execute(
                "SELECT id FROM contacts WHERE first_name = %s AND last_name = %s",
                (first_name, last_name),
            )
            row = cur.fetchone()
            return row["id"] if row else None


def update_contact(contact_id, **fields):
    if not fields:
        return
    set_clause = ", ".join(f"{k} = %s" for k in fields)
    values = list(fields.values()) + [contact_id]
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(f"UPDATE contacts SET {set_clause} WHERE id = %s", values)


def delete_contact(contact_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM contacts WHERE id = %s", (contact_id,))


def get_all_contacts():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM contacts ORDER BY last_name, first_name")
            return cur.fetchall()


def get_contact(contact_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM contacts WHERE id = %s", (contact_id,))
            return cur.fetchone()


# ---------- Interactions ----------

def add_interaction(contact_id, date_str=None, itype="Note", notes=""):
    date_str = date_str or date.today().isoformat()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO interactions (contact_id, date, type, notes) VALUES (%s, %s, %s, %s)",
                (contact_id, date_str, itype, notes),
            )
            return cur.lastrowid


def get_interactions(contact_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM interactions WHERE contact_id = %s ORDER BY date DESC",
                (contact_id,),
            )
            return cur.fetchall()


def get_all_interactions():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM interactions ORDER BY date DESC")
            return cur.fetchall()


def last_interaction_date(contact_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT MAX(date) as d FROM interactions WHERE contact_id = %s",
                (contact_id,),
            )
            row = cur.fetchone()
            return row["d"] if row and row["d"] else None


def interaction_count_since(contact_id, since_date_str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) as c FROM interactions WHERE contact_id = %s AND date >= %s",
                (contact_id, since_date_str),
            )
            row = cur.fetchone()
            return row["c"] if row else 0


def get_interaction_stats_bulk(window_days=180):
    """
    Fetches 'last interaction date' and 'interaction count in the last
    window_days' for EVERY contact in just 2 queries total, instead of
    2 queries per contact. This is what makes the Dashboard, Contacts,
    and Network Graph pages fast even with hundreds of contacts.

    Returns (last_dates, counts):
      last_dates: dict contact_id -> last interaction date string (or absent if none)
      counts:     dict contact_id -> number of interactions in the window (or absent if 0)
    """
    window_start = (date.today() - timedelta(days=window_days)).isoformat()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT contact_id, MAX(date) as last_date FROM interactions GROUP BY contact_id")
            last_dates = {row["contact_id"]: row["last_date"] for row in cur.fetchall()}

            cur.execute(
                "SELECT contact_id, COUNT(*) as c FROM interactions WHERE date >= %s GROUP BY contact_id",
                (window_start,),
            )
            counts = {row["contact_id"]: row["c"] for row in cur.fetchall()}
    return last_dates, counts


# ---------- Connections (contact <-> contact ties) ----------

def add_connection(contact_a, contact_b, label=""):
    a, b = sorted([contact_a, contact_b])
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM connections WHERE contact_a = %s AND contact_b = %s", (a, b)
            )
            if cur.fetchone():
                return None
            cur.execute(
                "INSERT INTO connections (contact_a, contact_b, label) VALUES (%s, %s, %s)",
                (a, b, label),
            )
            return cur.lastrowid


def get_all_connections():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM connections")
            return cur.fetchall()


def delete_connection(connection_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM connections WHERE id = %s", (connection_id,))
