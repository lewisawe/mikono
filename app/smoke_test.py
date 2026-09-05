#!/usr/bin/env python3
"""Cortex smoke test for Mikono.

Confirms key-pair auth works AND that the specific Cortex functions/models we
depend on are available in this account's region, BEFORE running the full
pipeline. Cheap to run; catches region/model mismatches early.
"""
import sys
import snowflake.connector
from cryptography.hazmat.primitives import serialization

KEY_PATH = ".secrets/mikono_rsa_key.p8"
ACCOUNT = "XUBWKQN-VGC59325"
USER = "LEWISAWE"
ROLE = "ACCOUNTADMIN"


def load_private_key():
    with open(KEY_PATH, "rb") as f:
        p = serialization.load_pem_private_key(f.read(), password=None)
    return p.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def main():
    conn = snowflake.connector.connect(
        account=ACCOUNT,
        user=USER,
        role=ROLE,
        private_key=load_private_key(),
    )
    cur = conn.cursor()
    print("connected OK")

    # Ensure a warehouse exists to run Cortex on.
    cur.execute("CREATE WAREHOUSE IF NOT EXISTS MIKONO_WH "
                "WAREHOUSE_SIZE='XSMALL' AUTO_SUSPEND=60 AUTO_RESUME=TRUE "
                "INITIALLY_SUSPENDED=FALSE")
    cur.execute("USE WAREHOUSE MIKONO_WH")

    # 1) Embedding: confirm model name + vector dimension.
    try:
        cur.execute(
            "SELECT ARRAY_SIZE(SNOWFLAKE.CORTEX.EMBED_TEXT_768("
            "'snowflake-arctic-embed-m-v1.5', 'I fix broken laptops')::ARRAY)"
        )
        dim = cur.fetchone()[0]
        print(f"EMBED_TEXT_768 OK, dimension = {dim}")
    except Exception as e:
        print(f"EMBED_TEXT_768 FAILED: {e}")

    # 2) COMPLETE: confirm an LLM model is available.
    for model in ("mistral-large2", "llama3.1-8b", "snowflake-arctic"):
        try:
            cur.execute(
                f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{model}', 'Say OK.')"
            )
            out = cur.fetchone()[0]
            print(f"COMPLETE('{model}') OK -> {out[:40]!r}")
            break
        except Exception as e:
            print(f"COMPLETE('{model}') failed: {str(e)[:80]}")

    # 3) CLASSIFY_TEXT: confirm available.
    try:
        cur.execute(
            "SELECT SNOWFLAKE.CORTEX.CLASSIFY_TEXT("
            "'I repair computers', ['tech repair','teaching','transport']):label::STRING"
        )
        print(f"CLASSIFY_TEXT OK -> {cur.fetchone()[0]!r}")
    except Exception as e:
        print(f"CLASSIFY_TEXT failed: {str(e)[:80]}")

    cur.close()
    conn.close()
    print("smoke test done")


if __name__ == "__main__":
    sys.exit(main())
