# Mikono — Demo Script

A tight walkthrough for the judges and the recorded video. Target: 2 minutes.
Everything runs on Snowflake Cortex, live.

## Setup before recording
- Pipeline has run (8 causes, 8 volunteers, matches built).
- App open on the Match board tab.
- Have two typed examples ready to paste (below).

## Beat 1 — The idea (15s)
"Every other giving tool moves money. Mikono moves hands. People post skills and
time, small causes post what they need, and Snowflake Cortex matches them by
meaning, not keywords."

## Beat 2 — The match board (35s)
Scroll the cards. Stop on **Uhuru Primary School ↔ Amina**.
- Read the Need: *"computer lab machines will not switch on."*
- Read the Offer: *"I fix broken laptops."*
- Point at the two bars: **Cortex semantic match 0.7-ish**, **Keyword overlap: 0
  shared words.**
"Zero shared words. A keyword search finds nothing here. Cortex pairs them
because it understands the meaning. That's the whole product in one card."

Point at the **proximity chip** (same town) and the **2nd choice** line.
"It's location-aware too, and it always shows its runner-up, so the ranking is
transparent."

## Beat 3 — Live matching, proof it's not hardcoded (45s)
Go to **I need help**. Paste:
> Our children's clinic keeps losing patient records because the computers freeze, and we have no budget for a technician.
Click **Find volunteers**.
- Watch the spinner ("Cortex is reading your need...").
- Show **"Cortex read your text as: tech repair"** and Amina coming back Strong.
"Brand-new sentence, never seen before, matched live in the warehouse."

Now paste something with no fit, in **I can help**:
> I can offer free legal advice on tenancy disputes.
"No cause here needs a lawyer, so it honestly says no strong match instead of
forcing a bad one. Calibrated, not hype."

## Beat 4 — Under the hood (20s)
"Four Cortex functions do all the work, in SQL: EMBED_TEXT_768 for the vectors,
VECTOR_COSINE_SIMILARITY to rank, CLASSIFY_TEXT for categories, and COMPLETE
writes the plain-language reason on each card. No external model, no data leaving
Snowflake. The app is Streamlit in Snowflake."

## Beat 5 — Close (5s)
"Mikono. Swahili for hands. Generosity you can give even when you have no money
to give."

## Backup facts (if asked)
- Blend: 70% semantic + 15% category + 15% same-location.
- verify_matching.py proves keyword overlap scores the hardest pairs at 0.0.
- Public demo runs on a read-only user, capped by a resource monitor.
