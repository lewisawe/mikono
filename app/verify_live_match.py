#!/usr/bin/env python3
"""Verify the UI's live ad-hoc matching queries work (new need + new offer)."""
import snowflake.connector
from cryptography.hazmat.primitives import serialization

KEY_PATH = ".secrets/mikono_rsa_key.p8"
ACCOUNT, USER, ROLE = "XUBWKQN-VGC59325", "LEWISAWE", "ACCOUNTADMIN"
EMBED_MODEL = "snowflake-arctic-embed-m-v1.5"
CATS = ("['tech repair','teaching & tutoring','design & media','healthcare',"
        "'finance & bookkeeping','translation','transport & logistics',"
        "'web & online presence']")


def load_private_key():
    with open(KEY_PATH, "rb") as f:
        p = serialization.load_pem_private_key(f.read(), password=None)
    return p.private_bytes(
        serialization.Encoding.DER, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption())


def main():
    conn = snowflake.connector.connect(
        account=ACCOUNT, user=USER, role=ROLE, private_key=load_private_key())
    cur = conn.cursor()
    cur.execute("USE DATABASE MIKONO"); cur.execute("USE SCHEMA CORE")
    cur.execute("USE WAREHOUSE MIKONO_WH")

    # A brand-new NEED the seed data never saw, no keyword overlap with offers.
    need = "Our clinic's record computers keep crashing and we cannot afford IT support"
    esc = need.replace("'", "''")
    print(f"NEW NEED: {need!r}\n-> top volunteers:")
    cur.execute(f"""
        WITH q AS (
            SELECT SNOWFLAKE.CORTEX.EMBED_TEXT_768('{EMBED_MODEL}', '{esc}') AS emb,
                   SNOWFLAKE.CORTEX.CLASSIFY_TEXT('{esc}', {CATS}):label::STRING AS cat
        )
        SELECT o.volunteer_name, o.category,
               ROUND(0.8*VECTOR_COSINE_SIMILARITY(q.emb,o.embedding)
                     +0.2*IFF(q.cat=o.category,1,0),3) AS score
        FROM OFFERS o, q ORDER BY score DESC LIMIT 3
    """)
    for r in cur.fetchall():
        print("  ", r)

    # A brand-new OFFER.
    offer = "I am a plumber and can fix taps and pipes for free on Sundays"
    esc = offer.replace("'", "''")
    print(f"\nNEW OFFER: {offer!r}\n-> top causes:")
    cur.execute(f"""
        WITH q AS (
            SELECT SNOWFLAKE.CORTEX.EMBED_TEXT_768('{EMBED_MODEL}', '{esc}') AS emb,
                   SNOWFLAKE.CORTEX.CLASSIFY_TEXT('{esc}', {CATS}):label::STRING AS cat
        )
        SELECT n.org_name, n.category,
               ROUND(0.8*VECTOR_COSINE_SIMILARITY(q.emb,n.embedding)
                     +0.2*IFF(q.cat=n.category,1,0),3) AS score
        FROM NEEDS n, q ORDER BY score DESC LIMIT 3
    """)
    for r in cur.fetchall():
        print("  ", r)

    cur.close(); conn.close()
    print("\nlive-query check done")


if __name__ == "__main__":
    main()
