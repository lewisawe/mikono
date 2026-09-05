#!/usr/bin/env python3
"""Deploy the Streamlit-in-Snowflake app programmatically.

Uploads app/streamlit_app.py to a stage in MIKONO.CORE and creates a Streamlit
object bound to MIKONO_WH. Prints the app URL on success.
"""
import os
import sys
import snowflake.connector
from cryptography.hazmat.primitives import serialization

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
KEY_PATH = os.path.join(ROOT, ".secrets", "mikono_rsa_key.p8")
ACCOUNT, USER, ROLE = "XUBWKQN-VGC59325", "LEWISAWE", "ACCOUNTADMIN"
APP_FILE = os.path.join(HERE, "streamlit_app.py")


def load_private_key():
    with open(KEY_PATH, "rb") as f:
        p = serialization.load_pem_private_key(f.read(), password=None)
    return p.private_bytes(
        serialization.Encoding.DER,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )


def main():
    conn = snowflake.connector.connect(
        account=ACCOUNT, user=USER, role=ROLE, private_key=load_private_key())
    cur = conn.cursor()
    cur.execute("USE DATABASE MIKONO")
    cur.execute("USE SCHEMA CORE")
    cur.execute("USE WAREHOUSE MIKONO_WH")
    print("connected OK")

    # Stage to hold the app file.
    cur.execute("CREATE STAGE IF NOT EXISTS MIKONO_APP_STAGE "
                "DIRECTORY = (ENABLE = TRUE)")
    print("stage ready")

    # Upload the app file (OVERWRITE so re-deploys work).
    local = APP_FILE.replace("\\", "/")
    cur.execute(f"PUT 'file://{local}' @MIKONO_APP_STAGE "
                f"AUTO_COMPRESS=FALSE OVERWRITE=TRUE")
    print("uploaded streamlit_app.py")

    # Create/replace the Streamlit object.
    cur.execute("""
        CREATE OR REPLACE STREAMLIT MIKONO_APP
          ROOT_LOCATION = '@MIKONO.CORE.MIKONO_APP_STAGE'
          MAIN_FILE = 'streamlit_app.py'
          QUERY_WAREHOUSE = 'MIKONO_WH'
    """)
    print("streamlit object created")

    # Fetch the app URL.
    cur.execute("SHOW STREAMLITS LIKE 'MIKONO_APP'")
    rows = cur.fetchall()
    cols = [c[0].lower() for c in cur.description]
    if rows:
        row = dict(zip(cols, rows[0]))
        url_id = row.get("url_id")
        print("\n=== Streamlit deployed ===")
        print(f"Open in Snowsight: Projects > Streamlit > MIKONO_APP")
        if url_id:
            print(f"Direct URL id: {url_id}")
        print("account:", ACCOUNT)

    cur.close()
    conn.close()
    print("\ndeploy done")


if __name__ == "__main__":
    sys.exit(main())
