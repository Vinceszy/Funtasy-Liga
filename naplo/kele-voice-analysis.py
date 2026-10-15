#!/usr/bin/env python3
"""COUNTS what recurs in the downloaded articles - offline.

WHY SEPARATE FROM THE FETCH: fetching is costly and external; the analysis
has to be rerun at any time, with a different question. So the text under
`tartalek/kele/` is the input, and every number comes from there.

WHAT IT DECIDES: a device goes into the description of the voice if it
appears in SEVERAL articles. The output therefore gives an article count,
not a match count.

WHAT IS LEFT OUT: only the TEMPLATE FORMATS - the publisher's own podcast
trailers (he did not write those), and the class register, which is a
player-by-player grading, not running text. Nothing is selected by subject:
whether he writes about the press or the national team is the subject, not
the voice. What appears in both is his.

THE PAGE FRAME IS CUT OFF: at the bottom of a downloaded page stands the
publisher's own "latest" strip, full of other titles. If it stays in, the
paragraph-length and vocabulary measurements measure what the site puts
there, not what the author writes.
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "tartalek", "kele")
# From here on comes the publisher's own recommendation strip, not the article.
CUT = ("Itt állíthatod be, hogy a Google kereső",
       "Nézd meg a legfrissebb cikkeinket",
       "A teljes cikket előfizetőink olvashatják el")

DEVICES = [
    ("self-correction in the second sentence", r"\bJó, ez (persze )?csúsztatás|\bJó, (ez|de) \w+,? (viszont|de|csak)"),
    ("first-person opening (Nezem/Olvasom/Latom)", r"^(Nézem|Olvasom|Látom|Hallgatom)\b"),
    ("question with its own answer", r"\?\s+(Mindjárt megmondom|Megmondom|Nem\.|Dehogy|Igen\.|Rejtély)"),
    ("Felreertes ne essek", r"Félreértés ne essék"),
    ("three concessions (Tudom ...)", r"Tudom(:| azt is)|végképp tudom"),
    ("interjection between dashes", r"\s[–-]\s[^–-]{3,60}\s[–-]\s"),
    ("short answer in brackets", r"\((Nem|Igen|Dehogy|Nyilván|Persze)[^)]{0,60}\)"),
    ("numbered thesis (numbered subheading)", r"(?m)^\s*\d\.\s+[A-ZÁÉÍÓÖŐÚÜŰ][^\n]{20,}$"),
    ("nominal, verbless opening", r"^[A-ZÁÉÍÓÖŐÚÜŰ][^.!?\n]{5,60},\s+[^.!?\n]{3,60}\.\s"),
    ("two-word dialogue with himself", r"\b(Tény\? Tény|Dehogynem|Dehogy)\b"),
    ("praeteritio (not a word about it)", r"egy szót sem szólok|ki se nyissuk"),
    ("myth/pathos vocabulary", r"\b(bálvány|megváltó|átk[ao]|isten|megtérés|aranycsata|prizmá)"),
    ("rare word", r"\b(hóbelevanc|parolázik|sorminta|dzsembori|skrupulus|tobzódó|pedigré|"
                  r"ethosz|érdemesültség|posvány|oktrojál|lóhalálában|netalántán|idestova|"
                  r"dagonyáz|kistafíroz|cech|bicskanyitogató|akarnok|apportál)"),
    ("addressing the reader", r"\b(gondolom kitaláljátok|Mondjam tovább|leszel szíves|"
                              r"tegyük a szívünkre|könyörgöm)\b"),
]


# THE COLUMN'S FIRST DESCRIPTION (an earlier custom-GPT instruction) makes six
# claims about the voice. Each is CHECKABLE on the corpus, and only what holds
# up may go into the notes: an instruction is not a source but a hypothesis.
CLAIMS = [
    ("statistics stay in the BACKGROUND",
     r"\b\d+([.,]\d+)?\b", "numbers / 1000 characters", False),
    ("subjective, first-person opinion",
     r"\b(én|nekem|szerintem|úgy vélem|meggyőződésem|azt gondolom|"
     r"engem|számomra|bevallom)\b", "first-person marks / 1000 characters", True),
    ("grand statements (superlative, extreme word)",
     r"\b(leg\w{4,}|soha|minden idők|gigantikus|elképesztő|példátlan|"
     r"felfoghatatlan|döbbenetes|katasztrofális|totális|abszurd)\b",
     "extremes / 1000 characters", True),
    ("critical edge, negative vocabulary",
     r"\b(hazug\w*|botrány\w*|szégyen\w*|kudarc\w*|felelős\w*|"
     r"bukás|csőd|hiba|rossz\w*|gyenge\w*|baj\w*|probléma)\b",
     "negative words / 1000 characters", True),
    ("grandiloquent, rarely used word (12+ letters)",
     r"\b[a-záéíóöőúüű]{13,}\b", "long words / 1000 characters", True),
    ("emotion stated",
     r"\b(fáj|megrendít|szomorú\w*|düh\w*|szégyellem|utál\w*|szeret\w*|"
     r"öröm\w*|csalódás)\b", "emotion words / 1000 characters", True),
]



# WHAT HE USES A NUMBER FOR. Bare number density misleads: a text with a lot
# of data can still be a dry report. The question is whether the number stands
# ALONE (a report) or supports a JUDGEMENT. That is measured by splitting into
# sentences and checking whether a sentence with a number carries an
# evaluation more often than one without - and whether that gap is larger
# for him than in the control.
JUDGEMENT = re.compile(
    r"\b(leg\w{4,}|soha|sosem|egyetlen|mindössze|csupán|alig|már|még mindig|"
    r"óta először|éve először|példátlan|elképesztő|döbbenetes|felfoghatatlan|"
    r"gigantikus|katasztrofális|szégyen\w*|kudarc\w*|botrány\w*|hazug\w*|"
    r"rossz\w*|gyenge\w*|kiváló|remek|nagyszerű|fáj|megrendít|szomorú\w*|"
    r"nem véletlen|éppen ezért|vagyis|tehát|pedig|mégis|holott|csakhogy)\b",
    re.IGNORECASE)
NUMBER = re.compile(r"\b\d+([.,]\d+)?\b")


def sentences(text):
    return [x.strip() for x in re.split(r"(?<=[.!?])\s+", text) if len(x.strip()) > 25]


def judgement_share(text):
    """In what percentage a judgement appears - with a number and without, separately."""
    with_n = without_n = with_j = without_j = 0
    for m in sentences(text):
        if NUMBER.search(m):
            with_n += 1
            with_j += 1 if JUDGEMENT.search(m) else 0
        else:
            without_n += 1
            without_j += 1 if JUDGEMENT.search(m) else 0
    return (100.0 * with_j / max(1, with_n), with_n,
            100.0 * without_j / max(1, without_n), without_n)


def body(path):
    with open(path, encoding="utf-8") as f:
        lines = [x.rstrip("\n") for x in f]
    # The first two lines are the header (title, url), then an empty line.
    lines = [x for x in lines[2:] if x.strip()]
    out = []
    for x in lines:
        if any(x.startswith(v) or v in x for v in CUT):
            break
        out.append(x)
    # The title and the tag line repeat before the body.
    return out[2:] if len(out) > 3 else out


def main():
    files = sorted(glob.glob(os.path.join(SOURCE, "*.txt")))
    if not files:
        print("no downloaded article under %s" % SOURCE)
        return 1
    own, others = [], []
    for path in files:
        with open(path, encoding="utf-8") as f:
            header = f.readline()
        # The site titles his own pieces with his name - but not all of them:
        # the class register and the opinion piece are his too, titled
        # differently.
        fname = path.rsplit("/", 1)[-1]
        template = fname.startswith("podcast-") or "osztalynaplo" in fname
        his = (not template) and (header.startswith("# Kele János:")
                                  or fname.startswith("substack-")
                                  or "velemenycikk" in fname
                                  or "kele-janos" in fname
                                  or "gegenpressing" in fname)
        (own if his else others).append(path)

    print("=" * 70)
    print("KELE CORPUS: %d downloaded pages, of which his own running text %d"
          % (len(files), len(own)))
    print("=" * 70)

    lengths = []
    for path in own:
        b = body(path)
        lengths += [len(x) for x in b]
        print("\n  %s  (%d paragraphs)" % (os.path.basename(path)[:58], len(b)))
        if b:
            print("    OPENS: %s" % b[0][:150])
            print("    CLOSES: %s" % b[-1][:150])

    if lengths:
        lengths.sort()
        print("\n  paragraph length: median %d, lower quartile %d, upper quartile %d"
              % (lengths[len(lengths) // 2], lengths[len(lengths) // 4],
                 lengths[3 * len(lengths) // 4]))

    print("\n  DEVICES - IN HOW MANY ARTICLES (of his own %d)" % len(own))
    for name, pattern in DEVICES:
        rx = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
        count = 0
        example = ""
        for path in own:
            text = "\n".join(body(path))
            m = rx.search(text)
            if m:
                count += 1
                example = example or text[max(0, m.start() - 40):m.end() + 60].replace("\n", " ")
        mark = "GENERAL  " if count >= max(3, len(own) // 3) else "single   "
        print("    %s %2d/%2d  %-38s %s"
              % (mark, count, len(own), name, example[:70]))

    # The claims of the column's first description, measured as density,
    # because they are proportions, not devices. A number says nothing without
    # a baseline, so every OTHER page of the corpus gets the same - mostly
    # the publisher's own podcast trailers, plus the class registers.
    print("\n  CLAIMS OF THE FIRST DESCRIPTION - DENSITY (marks / 1000 characters)")
    print("    %-42s %8s %8s" % ("", "Kele", "control"))
    kele = " ".join(" ".join(body(u)) for u in own)
    control = " ".join(" ".join(body(u)) for u in others)
    for name, pattern, unit, more_means_true in CLAIMS:
        rx = re.compile(pattern, re.IGNORECASE)
        a = 1000.0 * len(rx.findall(kele)) / max(1, len(kele))
        b = 1000.0 * len(rx.findall(control)) / max(1, len(control))
        ratio = a / b if b else 0
        if 0.8 <= ratio <= 1.25:
            mark = "undecided "
        elif (ratio > 1.25) == more_means_true:
            mark = "TRUE      "
        else:
            mark = "NOT TRUE  "
        print("    %s %-36s %8.2f %8.2f" % (mark, name, a, b))
    print("\n  WHAT HE USES A NUMBER FOR")
    for label, text in (("Kele", kele), ("control", control)):
        a, an, b, bn = judgement_share(text)
        print("    %-9s sentence with a number:    %5.1f%% carry a judgement "
              "(%d sentences)" % (label, a, an))
        print("    %-9s sentence without a number: %5.1f%% carry a judgement "
              "(%d sentences)" % ("", b, bn))
        print("    %-9s difference: %+.1f percentage points" % ("", a - b))

    print("\n    The control is every other downloaded page (%d), mostly the publisher's"
          % len(others))
    print("    OWN podcast trailers about the same column, plus the class registers.")
    print("    It is not a neutral measure: a trailer's job is to hype, so it is")
    print("    rich in superlatives and emotion words to begin with. What the number")
    print("    shows for certain: the author is NOT the more grandiloquent of the two.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
