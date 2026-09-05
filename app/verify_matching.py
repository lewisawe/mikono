#!/usr/bin/env python3
"""verify_matching.py

A pure-Python mirror of the Mikono matching logic in sql/04_match.sql, used ONLY
to sanity-check the ranking approach locally (no Snowflake, no third-party deps).

The real engine is Snowflake Cortex: EMBED_TEXT_768 produces semantic vectors and
VECTOR_COSINE_SIMILARITY ranks them, blended with a CLASSIFY_TEXT category boost.
Here we substitute a trivial bag-of-words vector for the embedding so the SCORING
STRUCTURE (cosine + 0.2 category boost, top-1 per need) can be checked offline.

Because bag-of-words has no semantic understanding, some rows here will look weaker
than in Snowflake — that gap is exactly why Cortex embeddings matter. This script
proves the ranking math is correct, not that keywords are enough.
"""
import math
import re
from collections import Counter

# Same descriptions as data/seed_offers_needs.sql (kept in sync by hand).
OFFERS = {
    "Amina": ("tech repair", "I fix broken laptops and desktops reinstall operating systems replace failed hard drives"),
    "Brian": ("finance & bookkeeping", "qualified accountant help small organisations get books in order prepare financial statements"),
    "Cynthia": ("teaching & tutoring", "former primary school teacher tutor children in maths and reading"),
    "David": ("design & media", "graphic designer make posters flyers social media graphics for a good cause"),
    "Esther": ("healthcare", "registered nurse basic health check-ups hygiene and first aid"),
    "Felix": ("web & online presence", "build websites set up simple online presence for a group"),
    "Grace": ("translation", "speak english swahili luo translate documents interpret at meetings"),
    "Hassan": ("transport & logistics", "drive a pickup move furniture equipment supplies around town"),
}
NEEDS = {
    "Uhuru Primary School": ("tech repair", "computer lab machines will not switch on cannot afford technician children missing ICT lessons"),
    "Mama Watoto Childrens Home": ("teaching & tutoring", "help kids with schoolwork on weekends numbers and reading"),
    "Green Streets Initiative": ("web & online presence", "no way to tell people about clean-up events need help looking professional online"),
    "Coastal Health Outreach": ("healthcare", "community day need someone medical simple screenings teach basic hygiene"),
    "Bookmark Literacy Trust": ("translation", "donated books in english families read swahili need help making them accessible"),
    "Furaha Womens Group": ("finance & bookkeeping", "savings records in a notebook a mess need someone who understands money"),
    "Harvest Food Bank": ("transport & logistics", "receive food donations across town struggle to collect and deliver without transport"),
    "Sunrise Youth Centre": ("design & media", "want printed materials to promote free skills classes no one to design them"),
}

_word = re.compile(r"[a-z]+")


def vec(text):
    return Counter(_word.findall(text.lower()))


def cosine(a, b):
    common = set(a) & set(b)
    dot = sum(a[t] * b[t] for t in common)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def best_match(need_text, need_cat):
    nv = vec(need_text)
    ranked = []
    for name, (cat, text) in OFFERS.items():
        sim = cosine(nv, vec(text))
        blended = 0.8 * sim + 0.2 * (1 if cat == need_cat else 0)
        ranked.append((name, cat, round(sim, 3), round(blended, 3)))
    ranked.sort(key=lambda r: -r[3])
    return ranked[0]


def main():
    print("Local matching check (bag-of-words stand-in for Cortex embeddings)\n")
    correct = 0
    for org, (need_cat, need_text) in NEEDS.items():
        name, cat, sim, blended = best_match(need_text, need_cat)
        hit = "OK" if cat == need_cat else "MISS"
        if cat == need_cat:
            correct += 1
        print(f"[{hit}] {org:<28} -> {name:<8} "
              f"({cat}; sim={sim}, blended={blended})")
    print(f"\ncategory-correct top-1: {correct}/{len(NEEDS)}")
    print("Note: Cortex embeddings do markedly better than this bag-of-words "
          "mirror on low-keyword-overlap pairs. See sql/04_match.sql for the "
          "real engine and app/run_pipeline.py for verified live results.")


if __name__ == "__main__":
    main()
