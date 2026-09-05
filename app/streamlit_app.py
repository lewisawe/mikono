"""Mikono — Streamlit app for the DEV Weekend Challenge: Generosity Edition.

A generosity exchange for skills & time. Snowflake Cortex matches free-text
offers of help to free-text needs by MEANING, not keywords.

Runs two ways with no code change:
  * Inside Snowflake (Streamlit in Snowflake): uses the active Snowpark session.
  * On Streamlit Community Cloud / locally: connects with credentials from
    st.secrets or environment, as a read-only demo user.
"""
import os
import streamlit as st


def do_rerun():
    """Rerun the script across Streamlit versions. Streamlit in Snowflake may
    ship an older Streamlit where st.rerun() does not exist yet; fall back to
    the experimental name, and no-op if neither is present."""
    fn = getattr(st, "rerun", None) or getattr(st, "experimental_rerun", None)
    if fn:
        fn()


def get_session():
    """Active Snowpark session in SiS, else build one from secrets/env.
    Returns (session, can_write). The public demo user is read-only, so we
    hide write actions there."""
    try:
        from snowflake.snowpark.context import get_active_session
        return get_active_session(), True   # full session inside Snowflake
    except Exception:
        from snowflake.snowpark import Session
        cfg = None
        try:
            if "snowflake" in st.secrets:
                cfg = dict(st.secrets["snowflake"])
        except Exception:
            cfg = None
        if not cfg:
            cfg = {
                "account": os.environ.get("SNOWFLAKE_ACCOUNT"),
                "user": os.environ.get("SNOWFLAKE_USER"),
                "password": os.environ.get("SNOWFLAKE_PASSWORD"),
                "role": os.environ.get("SNOWFLAKE_ROLE", "MIKONO_READONLY"),
                "warehouse": os.environ.get("SNOWFLAKE_WAREHOUSE", "MIKONO_PUBLIC_WH"),
                "database": os.environ.get("SNOWFLAKE_DATABASE", "MIKONO"),
                "schema": os.environ.get("SNOWFLAKE_SCHEMA", "CORE"),
            }
        can_write = str(cfg.get("role", "")).upper() != "MIKONO_READONLY"
        return Session.builder.configs(cfg).create(), can_write


session, CAN_WRITE = get_session()

EMBED_MODEL = "snowflake-arctic-embed-m-v1.5"
LLM_MODEL = "llama3.1-8b"
CATEGORIES = [
    "tech repair", "teaching & tutoring", "design & media", "healthcare",
    "finance & bookkeeping", "translation", "transport & logistics",
    "web & online presence",
]

st.set_page_config(page_title="Mikono", layout="wide")

# ---- small style layer so cards read as a product, not a grid -----------
st.markdown(
    """
    <style>
      .hero {font-size:0.95rem; color:#5b6472;}
      .card {border:1px solid #e6e8ec; border-radius:14px; padding:18px 20px;
             margin-bottom:14px; background:#ffffff;
             box-shadow:0 1px 3px rgba(0,0,0,0.04);}
      .pair {font-size:1.05rem; font-weight:600; color:#1c2430;}
      .chip {display:inline-block; padding:2px 10px; border-radius:999px;
             font-size:0.72rem; font-weight:600; margin-right:6px;
             background:#eef2ff; color:#3949ab;}
      .reason {color:#374151; margin-top:2px; font-style:italic;}
      .reasonlbl {font-size:0.68rem; color:#8a93a0; text-transform:uppercase;
                  letter-spacing:0.04em; margin-top:10px;}
      .quote {color:#4b5563; font-size:0.86rem; margin-top:6px;}
      .meterlbl {font-size:0.72rem; color:#6b7280; margin:6px 0 2px;}
      .barwrap {background:#eceff3; border-radius:999px; height:9px; width:100%;}
      .barfill {height:9px; border-radius:999px;}
      .runner {font-size:0.76rem; color:#8a93a0; margin-top:12px;
               padding-top:8px; border-top:1px solid #f0f2f5;}
      .verdict-strong {color:#0f7b3f; font-weight:700;}
      .verdict-possible {color:#b26a00; font-weight:700;}
      .verdict-none {color:#9aa0a6; font-weight:700;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Mikono")
st.markdown(
    "<div class='hero'>A generosity exchange for skills and time — not money, "
    "<b>hands</b>. Snowflake Cortex matches offers of help to real needs by "
    "meaning, so <i>“I fix broken laptops”</i> finds <i>“our lab machines won’t "
    "switch on”</i> even with no shared words.</div>",
    unsafe_allow_html=True,
)


def cats_sql():
    return "[" + ",".join("'" + c + "'" for c in CATEGORIES) + "]"


def bar(score, hue):
    pct = max(0, min(100, int(score * 100)))
    return (f"<div class='barwrap'><div class='barfill' "
            f"style='width:{pct}%; background:{hue};'></div></div>")


def verdict(score):
    if score >= 0.7:
        return "<span class='verdict-strong'>Strong match</span>"
    if score >= 0.55:
        return "<span class='verdict-possible'>Possible match</span>"
    return "<span class='verdict-none'>No clear match yet</span>"


# ---- hero stats ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def stats():
    row = session.sql(
        "SELECT (SELECT COUNT(*) FROM NEEDS), (SELECT COUNT(*) FROM OFFERS), "
        "(SELECT COUNT(*) FROM MATCHES WHERE rank=1)"
    ).to_pandas().iloc[0]
    return int(row[0]), int(row[1]), int(row[2])


needs_n, offers_n, matches_n = stats()
c1, c2, c3 = st.columns(3)
c1.metric("Causes asking", needs_n)
c2.metric("Volunteers offering", offers_n)
c3.metric("Matches made", matches_n)

tab_board, tab_need, tab_offer = st.tabs(
    ["Match board", "I need help", "I can help"]
)


# ---- Match board: cards, not a table ------------------------------------
with tab_board:
    st.subheader("Who can help each cause")
    st.caption("Each match is computed live by Cortex. On every card, the "
               "**blue bar** is Cortex reading meaning; the **grey bar** is all "
               "a keyword search would find. The top cards share almost no words "
               "yet still match — that gap is the whole point.")
    if st.button("Refresh", key="refresh"):
        st.cache_data.clear()
        do_rerun()

    # ---- one Cortex call reasoning over the WHOLE board, not just pairs ----
    @st.cache_data(show_spinner=False)
    def insight():
        # Aggregate the board in SQL, then let COMPLETE narrate the state of
        # the exchange in one sentence. This shows Cortex reasoning across the
        # full dataset, the kind of read a coordinator would want at a glance.
        return session.sql(
            """
            WITH b AS (SELECT org_name, volunteer_name, match_score
                       FROM MATCHES WHERE rank=1),
            agg AS (
                SELECT COUNT(*) AS n,
                       SUM(IFF(match_score >= 0.7, 1, 0)) AS strong,
                       MAX_BY(org_name || ' with ' || volunteer_name, match_score) AS best_pair,
                       MIN_BY(org_name, match_score) AS weakest_cause,
                       ROUND(AVG(match_score), 2) AS avg_score
                FROM b
            )
            SELECT SNOWFLAKE.CORTEX.COMPLETE('llama3.1-8b',
                'You are a volunteer coordinator. In ONE short sentence, summarise '
                || 'the state of this matching board for a busy reader. '
                || n || ' causes matched, ' || strong || ' of them strongly '
                || '(score >= 0.7), average score ' || avg_score || '. '
                || 'Strongest pairing: ' || best_pair || '. '
                || 'The cause with the weakest match is ' || weakest_cause || '. '
                || 'Be concrete and encouraging, no preamble.') AS summary
            FROM agg
            """
        ).to_pandas().iloc[0]["SUMMARY"]

    st.info(insight())

    @st.cache_data(show_spinner="Cortex is matching...")
    def board():
        return session.sql(
            """
            WITH m AS (
                SELECT need_id, org_name, need_category, need_text, need_location,
                       volunteer_name, offer_category, offer_text, offer_location,
                       same_location, similarity, match_score, why_match
                FROM MATCHES WHERE rank=1
            ),
            stop AS (
                SELECT f.value::string AS w
                FROM TABLE(FLATTEN(INPUT => SPLIT(
                    'the,a,an,and,or,to,of,for,in,on,we,our,i,is,are,can,help,need,someone,with,it,at,as,but,not,have,this,that,they,them,you,your',
                    ','))) f
            ),
            nt AS (
                SELECT need_id, LOWER(f.value::string) AS w
                FROM m, LATERAL FLATTEN(SPLIT(need_text,' ')) f
            ),
            ot AS (
                SELECT need_id, LOWER(f.value::string) AS w
                FROM m, LATERAL FLATTEN(SPLIT(offer_text,' ')) f
            ),
            kw AS (
                SELECT nt.need_id, COUNT(DISTINCT nt.w) AS shared_words
                FROM nt JOIN ot ON nt.need_id=ot.need_id AND nt.w=ot.w
                WHERE nt.w NOT IN (SELECT w FROM stop) AND LENGTH(nt.w) > 2
                GROUP BY nt.need_id
            ),
            second AS (
                SELECT need_id, volunteer_name AS runner_up,
                       ROUND(match_score, 3) AS runner_up_score
                FROM MATCHES WHERE rank = 2
            )
            SELECT m.org_name, m.need_category, m.need_text, m.need_location,
                   m.volunteer_name, m.offer_category, m.offer_text,
                   m.offer_location, m.same_location,
                   m.similarity, m.match_score, m.why_match,
                   COALESCE(kw.shared_words, 0) AS shared_words,
                   s.runner_up, s.runner_up_score
            FROM m
            LEFT JOIN kw ON m.need_id = kw.need_id
            LEFT JOIN second s ON m.need_id = s.need_id
            -- Lead with the strongest STORY, not just the top score: a pair
            -- with zero shared words but a high match is the whole thesis in
            -- one card, so surface fewest-shared-words first, then by score.
            ORDER BY COALESCE(kw.shared_words, 0) ASC, m.match_score DESC
            """
        ).to_pandas()

    df = board()
    for _, r in df.iterrows():
        sem = float(r["SIMILARITY"])
        shared = int(r["SHARED_WORDS"])
        kw_hint = "0 shared words" if shared == 0 else f"{shared} shared words"
        same_loc = int(r["SAME_LOCATION"]) == 1
        prox = (f"same town ({r['NEED_LOCATION']})" if same_loc
                else f"{r['NEED_LOCATION']} to {r['OFFER_LOCATION']}")
        runner = ""
        if r["RUNNER_UP"]:
            runner = (f"<div class='runner'>2nd choice: {r['RUNNER_UP']} "
                      f"({float(r['RUNNER_UP_SCORE']):.2f})</div>")
        ncat = r["NEED_CATEGORY"] if str(r["NEED_CATEGORY"]).upper() != "UNCLASSIFIED" else "uncategorised"
        ocat = r["OFFER_CATEGORY"] if str(r["OFFER_CATEGORY"]).upper() != "UNCLASSIFIED" else "uncategorised"
        st.markdown(
            f"""
            <div class='card'>
              <div class='pair'>{r['ORG_NAME']} &nbsp;↔&nbsp; {r['VOLUNTEER_NAME']}</div>
              <span class='chip'>needs: {ncat}</span>
              <span class='chip'>offers: {ocat}</span>
              <span class='chip'>{prox}</span>
              <div class='quote'>Need: “{r['NEED_TEXT']}”</div>
              <div class='quote'>Offer: “{r['OFFER_TEXT']}”</div>
              <div class='reasonlbl'>Why Cortex paired them</div>
              <div class='reason'>{r['WHY_MATCH']}</div>
              <div class='meterlbl'>Cortex semantic match: {sem:.2f}</div>
              {bar(sem, '#3949ab')}
              <div class='meterlbl'>Keyword overlap: {kw_hint}</div>
              {bar(shared / 6.0, '#c0c5cc')}
              {runner}
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---- helper: live match one query text against a table ------------------
def live_match(text, table, name_col, cat_col, extra_col, extra_label):
    # A typed query has no location, so we use a 2-signal blend here
    # (semantic + category) with weights that keep the score on the same
    # 0..1 scale as the board. Parameter binding (?) keeps user text out of
    # the SQL string entirely, so quotes are safe and there is no injection.
    #
    # Bilingual support: many offers/needs in this context are written in
    # Swahili or Sheng. Cortex TRANSLATE normalises the query to English first
    # (the seed corpus is English), so "Ninaweza kutengeneza kompyuta" matches
    # the same causes as "I can repair computers". Detected language is shown.
    en_text = text
    detected = "en"
    try:
        trow = session.sql(
            "SELECT SNOWFLAKE.CORTEX.TRANSLATE(?, '', 'en') AS en_text",
            params=[text],
        ).to_pandas().iloc[0]
        candidate = (trow["EN_TEXT"] or "").strip()
        # TRANSLATE with source '' auto-detects; if it changed the text, the
        # input was not English. Compare case-insensitively, ignore trivial diffs.
        if candidate and candidate.lower() != text.strip().lower():
            en_text = candidate
            detected = "non-en"
    except Exception:
        # If TRANSLATE is unavailable in the region, fall back to raw text.
        en_text = text

    df = session.sql(
        f"""
        WITH q AS (
            SELECT SNOWFLAKE.CORTEX.EMBED_TEXT_768('{EMBED_MODEL}', ?) AS emb,
                   SNOWFLAKE.CORTEX.CLASSIFY_TEXT(?, {cats_sql()}):label::STRING AS cat
        )
        SELECT t.{name_col} AS name, t.{cat_col} AS cat,
               t.{extra_col} AS extra, t.location AS loc,
               VECTOR_COSINE_SIMILARITY(q.emb, t.embedding) AS sim,
               0.82*VECTOR_COSINE_SIMILARITY(q.emb, t.embedding)
                 + 0.18*IFF(q.cat=t.{cat_col},1,0) AS score,
               q.cat AS inferred
        FROM {table} t, q
        ORDER BY score DESC LIMIT 3
        """,
        params=[en_text, en_text],
    ).to_pandas()

    if df.empty:
        st.info("Nothing to match against yet.")
        return df

    if detected == "non-en":
        st.caption(f"Cortex translated your text to English first: "
                   f"*“{en_text}”*")

    inferred = df.iloc[0]["INFERRED"] or "UNCLASSIFIED"
    if inferred.upper() == "UNCLASSIFIED":
        st.caption("Cortex couldn't fit this into a known help category, "
                   "so matching relies on meaning alone.")
    else:
        st.caption(f"Cortex read your text as: **{inferred}**")

    top = float(df.iloc[0]["SCORE"])
    if top < 0.55:
        st.warning(
            "No strong match yet. That's honest — it means no one here offers "
            "quite what's needed. Here's the closest, in case it helps:"
        )
    for _, r in df.iterrows():
        sc = float(r["SCORE"])
        cat = r["CAT"] if r["CAT"] and str(r["CAT"]).upper() != "UNCLASSIFIED" else "uncategorised"
        st.markdown(
            f"""
            <div class='card'>
              <div class='pair'>{r['NAME']} &nbsp;·&nbsp; {verdict(sc)}</div>
              <span class='chip'>{cat}</span>
              <span class='chip'>{extra_label}: {r['EXTRA']}</span>
              <span class='chip'>location: {r['LOC']}</span>
              <div class='meterlbl'>Match strength: {sc:.2f}</div>
              {bar(sc, '#3949ab' if sc >= 0.55 else '#c0c5cc')}
            </div>
            """,
            unsafe_allow_html=True,
        )
    return df


def persist(text, kind, location):
    """Insert a new offer/need with a live embedding + category so it joins
    the exchange. Parameter-bound; user text never enters the SQL string."""
    loc = location.strip() or "unknown"
    if kind == "need":
        session.sql(
            f"""
            INSERT INTO NEEDS (need_id, org_name, location, urgency, description,
                               category, embedding)
            SELECT (SELECT COALESCE(MAX(need_id),0)+1 FROM NEEDS),
                   'You (demo)', ?, 'new', ?,
                   SNOWFLAKE.CORTEX.CLASSIFY_TEXT(?, {cats_sql()}):label::STRING,
                   SNOWFLAKE.CORTEX.EMBED_TEXT_768('{EMBED_MODEL}', ?)
            """,
            params=[loc, text, text, text],
        ).collect()
    else:
        session.sql(
            f"""
            INSERT INTO OFFERS (offer_id, volunteer_name, location, availability,
                                description, category, embedding)
            SELECT (SELECT COALESCE(MAX(offer_id),0)+1 FROM OFFERS),
                   'You (demo)', ?, 'flexible', ?,
                   SNOWFLAKE.CORTEX.CLASSIFY_TEXT(?, {cats_sql()}):label::STRING,
                   SNOWFLAKE.CORTEX.EMBED_TEXT_768('{EMBED_MODEL}', ?)
            """,
            params=[loc, text, text, text],
        ).collect()


# ---- I need help --------------------------------------------------------
with tab_need:
    st.subheader("Describe what your cause needs")
    st.caption("Plain language, English or Swahili — Cortex reads meaning and "
               "translates if needed. No need to guess keywords.")
    need_text = st.text_area(
        "What help do you need?",
        placeholder="e.g. Our clinic's record computers keep crashing and we can't afford IT support.",
        key="need_text",
    )
    add_need = st.checkbox("Also post this need to the board", key="add_need") if CAN_WRITE else False
    need_loc = ""
    if add_need:
        need_loc = st.text_input("Your town (helps local matching)",
                                 placeholder="e.g. Nairobi", key="need_loc")
    if st.button("Find volunteers", type="primary", key="need_btn") and need_text.strip():
        with st.spinner("Cortex is reading your need and matching..."):
            live_match(need_text, "OFFERS", "volunteer_name", "category",
                       "availability", "available")
            if add_need:
                persist(need_text, "need", need_loc)
                st.cache_data.clear()
                st.success("Posted. It now counts on the board above.")


# ---- I can help ---------------------------------------------------------
with tab_offer:
    st.subheader("Describe how you can help")
    st.caption("A weak result is honest: it means no cause here needs that yet.")
    offer_text = st.text_area(
        "What can you offer?",
        placeholder="e.g. I'm a plumber and can fix taps and pipes for free on Sundays.",
        key="offer_text",
    )
    add_offer = st.checkbox("Also post this offer to the board", key="add_offer") if CAN_WRITE else False
    offer_loc = ""
    if add_offer:
        offer_loc = st.text_input("Your town (helps local matching)",
                                  placeholder="e.g. Mombasa", key="offer_loc")
    if st.button("Find causes to help", type="primary", key="offer_btn") and offer_text.strip():
        with st.spinner("Cortex is reading your offer and matching..."):
            live_match(offer_text, "NEEDS", "org_name", "category",
                       "urgency", "urgency")
            if add_offer:
                persist(offer_text, "offer", offer_loc)
                st.cache_data.clear()
                st.success("Posted. It now counts on the board above.")


st.markdown("<hr style='border:none;border-top:1px solid #e6e8ec;margin:8px 0;'>",
            unsafe_allow_html=True)
st.caption("Built with Snowflake Cortex — EMBED_TEXT_768, CLASSIFY_TEXT, "
           "VECTOR_COSINE_SIMILARITY, TRANSLATE, COMPLETE — for the DEV Weekend "
           "Challenge: Generosity Edition. Mikono is Swahili for hands.")
