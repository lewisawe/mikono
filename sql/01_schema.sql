-- Mikono — Snowflake schema
-- A generosity exchange for skills & time. Cortex matches free-text OFFERS of
-- help to free-text NEEDS by semantic meaning, not keyword overlap.
--
-- Run order: 01_schema.sql -> 02_seed.sql -> 03_embed.sql -> 04_match.sql
--
-- Requires: a role with the CORTEX_USER database role (for Cortex AI functions).
-- Cortex must be available in your account region.

CREATE DATABASE IF NOT EXISTS MIKONO;
USE DATABASE MIKONO;
CREATE SCHEMA IF NOT EXISTS CORE;
USE SCHEMA CORE;

-- A warehouse for interactive Cortex + queries. XS is plenty for a demo.
CREATE WAREHOUSE IF NOT EXISTS MIKONO_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE;
USE WAREHOUSE MIKONO_WH;

-- OFFERS: someone volunteering a skill or time.
CREATE OR REPLACE TABLE OFFERS (
    offer_id        INTEGER,
    volunteer_name  STRING,
    location        STRING,
    availability    STRING,          -- free text, e.g. "weekends", "evenings after 6"
    description     STRING,          -- free text: what they can help with
    category        STRING,          -- filled later by Cortex CLASSIFY_TEXT
    embedding       VECTOR(FLOAT, 768), -- filled later by Cortex EMBED_TEXT_768
    created_at      TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- NEEDS: a cause / person asking for hands, not cash.
CREATE OR REPLACE TABLE NEEDS (
    need_id         INTEGER,
    org_name        STRING,
    location        STRING,
    urgency         STRING,          -- free text, e.g. "this week", "ongoing"
    description     STRING,          -- free text: what help is needed
    category        STRING,          -- filled later by Cortex CLASSIFY_TEXT
    embedding       VECTOR(FLOAT, 768), -- filled later by Cortex EMBED_TEXT_768
    created_at      TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
