-- Mikono — 04: the match
-- For every NEED, rank OFFERS by a BLENDED score built from three Cortex/data
-- signals:
--   * 0.70  semantic similarity of descriptions (Cortex embeddings, cosine)
--   * 0.15  category agreement (Cortex CLASSIFY_TEXT put both in same bucket)
--   * 0.15  same location (generosity is local; a nurse across the country
--           can't run a clinic day next week)
-- Skill stays dominant, so no one is matched to the wrong skill; proximity and
-- category break ties and reward realistic, actionable matches.
--
-- Then COMPLETE turns the pair into a one-line plain-language reason.

USE DATABASE MIKONO;
USE SCHEMA CORE;
USE WAREHOUSE MIKONO_WH;

CREATE OR REPLACE VIEW MATCHES AS
WITH scored AS (
    SELECT
        n.need_id,
        n.org_name,
        n.description       AS need_text,
        n.category          AS need_category,
        n.location          AS need_location,
        o.offer_id,
        o.volunteer_name,
        o.description       AS offer_text,
        o.category          AS offer_category,
        o.location          AS offer_location,
        o.availability,
        VECTOR_COSINE_SIMILARITY(n.embedding, o.embedding) AS similarity,
        IFF(n.category = o.category, 1, 0)                 AS same_category,
        IFF(n.location = o.location, 1, 0)                 AS same_location,
        (0.70 * VECTOR_COSINE_SIMILARITY(n.embedding, o.embedding)
         + 0.15 * IFF(n.category = o.category, 1, 0)
         + 0.15 * IFF(n.location = o.location, 1, 0))      AS blended_score,
        ROW_NUMBER() OVER (
            PARTITION BY n.need_id
            ORDER BY
                (0.70 * VECTOR_COSINE_SIMILARITY(n.embedding, o.embedding)
                 + 0.15 * IFF(n.category = o.category, 1, 0)
                 + 0.15 * IFF(n.location = o.location, 1, 0)) DESC
        ) AS rank
    FROM NEEDS n
    CROSS JOIN OFFERS o
)
SELECT
    need_id, org_name, need_text, need_category, need_location,
    offer_id, volunteer_name, offer_text, offer_category, offer_location,
    availability,
    ROUND(similarity, 3)     AS similarity,
    same_category,
    same_location,
    ROUND(blended_score, 3)  AS match_score,
    rank,
    SNOWFLAKE.CORTEX.COMPLETE(
        'llama3.1-8b',
        'You match volunteers to community causes. In ONE short sentence, name '
        || 'the concrete first step this volunteer could take to help this cause. '
        || 'Start with the volunteer''s name and a verb. Be specific and practical, '
        || 'not generic. '
        || 'Cause (' || org_name || ', ' || need_location || '): ' || need_text
        || ' Volunteer (' || volunteer_name || ', ' || offer_location || ', '
        || 'available ' || availability || '): ' || offer_text
        || ' Answer in one plain sentence, no preamble.'
    ) AS why_match
FROM scored
WHERE rank <= 2;   -- top 2 offers per need

-- The demo query: best volunteer for each cause, ranked, with the reason.
SELECT
    org_name        AS "Cause",
    need_category   AS "Needs",
    volunteer_name  AS "Volunteer",
    offer_category  AS "Offers",
    IFF(same_location = 1, 'same town', 'different town') AS "Proximity",
    match_score     AS "Score",
    why_match       AS "Why they fit"
FROM MATCHES
WHERE rank = 1
ORDER BY need_id;
