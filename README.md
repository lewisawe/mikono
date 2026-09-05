# Mikono — a generosity exchange for skills and time

Most giving tools move money. Mikono moves **hands**. People post what they can
do (fix laptops, tutor kids, drive a pickup, translate) and small causes post
what they need, both in plain language. **Snowflake Cortex matches them by
meaning**, so "I repair computers" finds "our lab machines won't switch on"
even though the two sentences share no words.

Built for the DEV Weekend Challenge: Generosity Edition.

## Why meaning, not keywords

Real needs and real offers almost never use the same words. A school writes
"the computer lab machines will not switch on." A volunteer writes "I fix broken
laptops." Keyword search scores that pair **0.0** (see `app/verify_matching.py`).
Cortex embeddings score it **0.75**. That gap is the whole reason this runs on
Snowflake Cortex instead of `LIKE '%...%'`.

## How it works

The data flows one way: **offers + needs → Cortex → matches.**

1. `sql/01_schema.sql` creates two tables (OFFERS, NEEDS), each with a free-text
   description and a `VECTOR(FLOAT, 768)` embedding column.
2. `data/seed_offers_needs.sql` seeds realistic offers and needs, written so the
   right matches share *meaning*, not keywords.
3. `sql/03_embed.sql` enriches every row with two Cortex calls:
   `EMBED_TEXT_768` (a semantic vector) and `CLASSIFY_TEXT` (a category label).
4. `sql/04_match.sql` ranks offers against needs with a **blended score**:
   `0.8 * VECTOR_COSINE_SIMILARITY + 0.2 * category-agreement`. The category
   boost (also from Cortex) corrects the rare case where shared context words
   fool raw similarity.
5. `app/streamlit_app.py` is a Streamlit-in-Snowflake app: a live match board,
   plus two tabs where anyone can type a fresh need or offer and get matched on
   the spot (embed + classify + cosine, computed live in the warehouse).

Four Cortex capabilities, all in-warehouse: `EMBED_TEXT_768`, `CLASSIFY_TEXT`,
`VECTOR_COSINE_SIMILARITY`, and `COMPLETE` (which writes the plain-language
"why they fit" line for each match).

## Project layout

```
sql/
  01_schema.sql            database, warehouse, OFFERS + NEEDS tables
  03_embed.sql             Cortex EMBED_TEXT_768 + CLASSIFY_TEXT enrichment
  04_match.sql             blended semantic match view + demo query
data/
  seed_offers_needs.sql    realistic offers and needs
app/
  run_pipeline.py          one-shot: schema -> seed -> embed -> match
  deploy_streamlit.py      uploads + creates the Streamlit-in-Snowflake app
  streamlit_app.py         the app (match board + live matching)
  smoke_test.py            confirms Cortex models are available in your region
  verify_matching.py       pure-Python mirror of the ranking (no Snowflake)
```

## Run it against your Snowflake account

1. Install dependencies:
   ```
   pip install "snowflake-connector-python[pandas]" snowflake-snowpark-python cryptography
   ```
2. Provide credentials one of two ways:
   - **Key-pair** (used here): put the private key at
     `.secrets/mikono_rsa_key.p8` and register the public key with
     `ALTER USER <you> SET RSA_PUBLIC_KEY='...'`.
   - **Password / env**: set `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`,
     `SNOWFLAKE_PASSWORD` (and optionally `ROLE`) in the environment or a `.env`.
3. Confirm Cortex is available in your region:
   ```
   python app/smoke_test.py
   ```
4. Build everything in Snowflake:
   ```
   python app/run_pipeline.py
   ```
5. Deploy the Streamlit-in-Snowflake app:
   ```
   python app/deploy_streamlit.py
   ```
   Then open Snowsight -> Projects -> Streamlit -> MIKONO_APP.

## Public demo (Streamlit Community Cloud)

A Streamlit-in-Snowflake app lives inside your account, so judges can't open it.
To publish a clickable demo:

1. Create a locked-down read-only user (read + Cortex only, capped warehouse):
   ```
   -- run sql/05_readonly_role.sql as ACCOUNTADMIN, then set a password:
   ALTER USER MIKONO_DEMO SET PASSWORD = '<strong password>';
   ```
2. Deploy `app/streamlit_app.py` on Streamlit Community Cloud, and paste the
   block from `.streamlit/secrets.toml.example` into the app's Secrets, using the
   `MIKONO_DEMO` / `MIKONO_READONLY` credentials.

The app detects its environment: inside Snowflake it uses the active Snowpark
session (writes enabled); on Community Cloud it connects as the read-only user
and hides the "post to the board" actions.

## Verify the logic offline (no Snowflake)

```
python app/verify_matching.py
```
This reimplements the ranking in plain Python. It deliberately uses a
bag-of-words stand-in for the embedding, so you can watch keyword similarity
score the hardest pairs at 0.0 while the category boost still lands them, which
is exactly why the real engine uses Cortex embeddings.

## Model notes

- Region-dependent Cortex models: this account has `EMBED_TEXT_768`
  (`snowflake-arctic-embed-m-v1.5`, 768-dim), `CLASSIFY_TEXT`, and
  `COMPLETE` on `llama3.1-8b`. `smoke_test.py` detects what your region exposes.
- The blend weights (0.8 / 0.2) are a simple, defensible default. Both signals
  come from Cortex; tune in `sql/04_match.sql`.
- Seed data is synthetic but realistic (Kenyan SME / community context).

Decision support for connecting willing hands to real needs, not a hiring
platform.
