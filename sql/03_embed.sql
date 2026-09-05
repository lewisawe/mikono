-- Mikono — 03: enrich with Cortex
-- Two Cortex calls per row:
--   1. EMBED_TEXT_768  -> a vector for semantic matching
--   2. CLASSIFY_TEXT   -> a human-readable category, used for filtering/labels
--
-- Model note: 'snowflake-arctic-embed-m-v1.5' returns 768-dim vectors (matches
-- the VECTOR(FLOAT, 768) columns). If your account exposes a different embed
-- model/size, change BOTH the column dimension and the model name to match.

USE DATABASE MIKONO;
USE SCHEMA CORE;
USE WAREHOUSE MIKONO_WH;

-- Categories we classify help into (inlined as an array literal for robustness).

-- ---- OFFERS -------------------------------------------------------------
UPDATE OFFERS
SET embedding = SNOWFLAKE.CORTEX.EMBED_TEXT_768(
        'snowflake-arctic-embed-m-v1.5',
        description
    );

UPDATE OFFERS
SET category = SNOWFLAKE.CORTEX.CLASSIFY_TEXT(
        description,
        ['tech repair','teaching & tutoring','design & media','healthcare','finance & bookkeeping','translation','transport & logistics','web & online presence']
    ):label::STRING;

-- ---- NEEDS --------------------------------------------------------------
UPDATE NEEDS
SET embedding = SNOWFLAKE.CORTEX.EMBED_TEXT_768(
        'snowflake-arctic-embed-m-v1.5',
        description
    );

UPDATE NEEDS
SET category = SNOWFLAKE.CORTEX.CLASSIFY_TEXT(
        description,
        ['tech repair','teaching & tutoring','design & media','healthcare','finance & bookkeeping','translation','transport & logistics','web & online presence']
    ):label::STRING;

-- Sanity check: every row should now have a category and a non-null embedding.
SELECT 'offers' AS tbl, COUNT(*) AS row_count, COUNT(embedding) AS embedded, COUNT(category) AS categorized FROM OFFERS
UNION ALL
SELECT 'needs',  COUNT(*),               COUNT(embedding),      COUNT(category)          FROM NEEDS;
