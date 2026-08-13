"""
Database connection for ADAA (PostgreSQL, hosted on Supabase).

Why this file is not just one line
----------------------------------
Supabase gives you a connection string that looks like this:

    postgresql://postgres:[YOUR-PASSWORD]@db.xxxx.supabase.co:5432/postgres

Two things go wrong almost every time:

1. The square brackets are only a placeholder. They must be deleted, but
   they are easy to leave behind.
2. If the password contains a character like "@", ":", "/" or "#", the URL
   becomes ambiguous and the connection fails with a confusing "could not
   resolve host" error.

Rather than asking you to hand-encode your password, ``normalize_database_url``
repairs both problems automatically. You can paste the connection string
exactly as Supabase gives it to you, type your real password in place of
[YOUR-PASSWORD], and it will work.
"""

from urllib.parse import quote

import psycopg
from psycopg.rows import dict_row

from app.config import settings


def normalize_database_url(url: str) -> str:
    """
    Return a connection URL that PostgreSQL can parse safely.

    Removes leftover [ ] around the password and percent-encodes any
    character that would otherwise confuse the URL parser.
    """
    if not url or "://" not in url:
        return url

    scheme, rest = url.split("://", 1)

    # No credentials in the string: nothing to repair.
    if "@" not in rest:
        return url

    # The host is after the LAST "@". Anything before it is the credentials,
    # even if the password itself contains an "@".
    credentials, host = rest.rsplit("@", 1)
    user, separator, password = credentials.partition(":")

    if not separator:  # a user but no password
        return url

    # Drop the placeholder brackets if they were left in.
    if password.startswith("[") and password.endswith("]"):
        password = password[1:-1]

    # If the password is already encoded, leave it alone. Otherwise encode it.
    if "%" not in password:
        password = quote(password, safe="")

    return f"{scheme}://{user}:{password}@{host}"


def get_database_url() -> str:
    """The connection URL for this application, ready to use."""
    if not settings.database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. Copy the connection string from the "
            "Supabase dashboard (Project Settings -> Database -> Connection "
            "string -> URI) into your .env file."
        )
    return normalize_database_url(settings.database_url)


def connect() -> psycopg.Connection:
    """
    Open a connection to the ADAA database.

    Use it with "with", so the connection always closes:

        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute("select count(*) from workers")
    """
    return psycopg.connect(get_database_url(), connect_timeout=15)


def fetch_all(sql: str, params: tuple = ()) -> list[dict]:
    """
    Run a query and return every row as a dictionary.

    Dictionaries are used because FastAPI turns them straight into JSON.
    """
    with connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, params)
            return cur.fetchall()


def fetch_one(sql: str, params: tuple = ()) -> dict | None:
    """Run a query and return the first row, or None if there is no row."""
    with connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, params)
            return cur.fetchone()


# ---------------------------------------------------------------------------
# Locations
# ---------------------------------------------------------------------------
#
# ADAA has no separate table of places. A location is simply somewhere
# workers are recorded, so the list comes from the workers themselves
# rather than from a hard-coded list that could drift out of date.

_LOCATION_SQL = """
    select location_name as name,
           round(avg(location_lat)::numeric, 6)::float8 as lat,
           round(avg(location_lng)::numeric, 6)::float8 as lng,
           count(*) as workers
      from workers
     where location_name is not null
"""


def all_locations() -> list[dict]:
    """Every place ADAA has workforce in, busiest first."""
    return fetch_all(
        _LOCATION_SQL + " group by location_name order by count(*) desc, location_name"
    )


def find_location(name: str) -> dict | None:
    """Turn a place name such as 'Guntur' into coordinates, or None."""
    return fetch_one(
        _LOCATION_SQL + " and lower(location_name) = lower(%s) group by location_name",
        (name,),
    )
