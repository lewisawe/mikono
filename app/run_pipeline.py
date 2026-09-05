#!/usr/bin/env python3
"""Run the full Mikono pipeline against Snowflake and print real matches.

Credential resolution (first match wins, per field):
  1. SNOWFLAKE_<FIELD> from the OS environment
  2. SNOWFLAKE_<FIELD> or bare <field> from a .env / connections.toml file
Auth:
  * key-pair if a private key file is present (.secrets/mikono_rsa_key.p8 or
    SNOWFLAKE_PRIVATE_KEY_PATH), else
  * password (SNOWFLAKE_PASSWORD / password in .env)

Usage:
    python app/run_pipeline.py
"""
import os
import sys
import snowflake.connector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# Defaults for this account; overridable via env/.env.
DEFAULTS = {"account": "XUBWKQN-VGC59325", "user": "LEWISAWE", "role": "ACCOUNTADMIN"}
DEFAULT_KEY_PATH = os.path.join(ROOT, ".secrets", "mikono_rsa_key.p8")

SQL_FILES = [
    os.path.join(ROOT, "sql", "01_schema.sql"),
    os.path.join(ROOT, "data", "seed_offers_needs.sql"),
    os.path.join(ROOT, "sql", "03_embed.sql"),
    os.path.join(ROOT, "sql", "04_match.sql"),
]

PLACEHOLDERS = {"", "<none selected>", "none", "null"}


def load_dotenv():
    """Read KEY=value and key = "value" pairs from .env / connections.toml."""
    found = {}
    for path in (os.path.join(ROOT, ".env"), os.path.join(os.getcwd(), ".env"),
                 os.path.join(ROOT, "connections.toml")):
        if not os.path.isfile(path):
            continue
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("["):
                    continue
                if line.lower().startswith("export "):
                    line = line[7:]
                if "=" not in line:
                    continue
                k, v = line.split("=", 1)
                v = v.strip()
                if v and v[0] in "\"'":
                    q = v[0]
                    end = v.find(q, 1)
                    v = v[1:end] if end != -1 else v[1:]
                elif " #" in v:
                    v = v.split(" #", 1)[0].strip()
                found[k.strip()] = v
    return found


def resolve():
    dot = load_dotenv()

    def ok(v):
        return v is not None and v.strip().lower() not in PLACEHOLDERS

    def pick(field, default=None):
        F = field.upper()
        env_val = os.environ.get(f"SNOWFLAKE_{F}")
        if ok(env_val):
            return env_val.strip()
        for key in (f"SNOWFLAKE_{F}", field, field.upper(), field.lower()):
            if key in dot and ok(dot[key]):
                return dot[key].strip()
        return default

    params = {}
    for field in ("account", "user", "password", "role", "warehouse",
                  "database", "schema"):
        val = pick(field, DEFAULTS.get(field))
        if val is not None:
            params[field] = val
    return params


def load_private_key(path):
    from cryptography.hazmat.primitives import serialization
    with open(path, "rb") as f:
        p = serialization.load_pem_private_key(f.read(), password=None)
    return p.private_bytes(
        serialization.Encoding.DER,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )


def connect():
    params = resolve()
    key_path = os.environ.get("SNOWFLAKE_PRIVATE_KEY_PATH", DEFAULT_KEY_PATH)
    if os.path.isfile(key_path):
        params.pop("password", None)
        params["private_key"] = load_private_key(key_path)
        auth = f"key-pair ({os.path.basename(key_path)})"
    elif params.get("password"):
        auth = "password"
    else:
        raise SystemExit(
            "No auth found. Provide a key at .secrets/mikono_rsa_key.p8 "
            "(or SNOWFLAKE_PRIVATE_KEY_PATH) or a password in .env."
        )
    for req in ("account", "user"):
        if not params.get(req):
            raise SystemExit(f"Missing '{req}'.")
    print(f"connecting as {params['user']}@{params['account']} via {auth}")
    return snowflake.connector.connect(**params)


def main():
    conn = connect()
    print("connected OK\n")
    for path in SQL_FILES:
        rel = os.path.relpath(path, ROOT)
        print(f"--- running {rel} ---")
        with open(path) as f:
            sql_text = f.read()
        cursors = conn.execute_string(sql_text)
        last = cursors[-1]
        if last.description:
            cols = [c[0] for c in last.description]
            print("  columns:", cols)
            for row in last.fetchall():
                print("  ", row)
        print()
    conn.close()
    print("pipeline done")


if __name__ == "__main__":
    sys.exit(main())
