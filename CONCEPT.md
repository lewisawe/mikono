# Mikono — Primary Idea (Snowflake Cortex)

DEV Weekend Challenge: Generosity Edition. Target category: Best Use of Snowflake.
Submissions due: 2026-09-07 06:59 UTC.

## One-liner
A generosity exchange for skills and time (not money), where Snowflake Cortex
semantically matches free-text offers of help to free-text needs.

## Why it can win
- Breaks the money-only assumption that every other entry shares.
- Rides the proven signal that non-money generosity resonates (see "Sprinkle",
  the leading donated-goods entry).
- Uses Cortex for its real strength: semantic search + CLASSIFY_TEXT over messy
  free text. Not a bolt-on chatbot.
- Snowflake category pool is thin, improving odds.

## The problem
Small causes need hands, not just cash: "our school laptops are broken",
"we need someone to tutor on Saturdays". Willing helpers exist but there is no
smart way to match "I can fix laptops on weekends" to that need. Keyword search
fails because the words never overlap.

## Core flow (minimum winning demo)
1. People post OFFERS of skills/time (free text) and NEEDS (free text).
2. Cortex embeds/classifies both and finds semantic matches (no keyword overlap
   required).
3. A match view shows why they fit, ranked.
4. Cortex Analyst: ask "who can help the school in plain language?".

## Cortex functions to use
- Semantic matching (EMBED_TEXT / VECTOR similarity or Cortex Search)
- CLASSIFY_TEXT (bucket offers and needs into categories)
- SUMMARIZE (explain a match in plain language)
- Optional: TRANSLATE (Swahili/Sheng offers -> English) for the KE context

## Stack (proposed)
- Snowflake trial (120-day free), Cortex enabled region.
- Streamlit-in-Snowflake for the frontend (tightest "best use of Snowflake").
- Synthetic seed data (realistic offers + needs).

## Author hook
Coordinated Red Cross COVID distributions and volunteer teams. The gap between
willing helpers and real needs is lived experience, not hypothetical.

## Status
- [ ] Snowflake trial + Cortex confirmed
- [ ] Schema + seed data
- [ ] Cortex matching SQL
- [ ] Streamlit UI
- [ ] README + demo video
- [ ] DEV writeup
