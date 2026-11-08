#!/usr/bin/env python3
"""Builds an XMLTV guide for StreamVault whose channel ids/display-names are the provider's exact
"ES - …" channel names, so StreamVault's normalized-name matcher maps every channel automatically.

Source: davidmuma EPG_dobleM guiatv.xml.gz. Usage: make_epg.py channels.txt guide.xml.gz
"""
import gzip, re, sys, unicodedata, urllib.request
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

SRC = "https://raw.githubusercontent.com/davidmuma/EPG_dobleM/master/guiatv.xml.gz"
QUALITY = re.compile(r"(?i)\b(F?HD|SD|UHD|4K(/UHD)?|HEVC|H265|720P?|1080P?|RAW|BACKUP|LOW|HQ)\b")
PREFIX = re.compile(r"^\s*ES(\s+[A-Z]{1,3})?\s*[-|:]\s*")
MARKS = ["ᴿᴬᵂ", "ᴴᴰ", "◉", "ᶠᴴᴰ", "ᵁᴴᴰ"]
# Spanish programme-show words StreamVault's (English/Portuguese) classifier doesn't know.
SHOW = [(re.compile(r"(?i)^(res[uú]men|resúmenes|lo mejor|goles de)"), "Highlights"),
        (re.compile(r"(?i)^(previa|pre-?partido|la previa)"), "Preview"),
        (re.compile(r"(?i)^(post-?partido|postpartido)"), "Post-game"),
        (re.compile(r"(?i)\b(reposici[oó]n|diferido)\b"), "Replay")]
# Provider base-name keys that differ from the guide's.
ALIASES = {"vamos": "m+vamos", "daznformula1": "daznf1"}


def strip_marks(s):
    for m in MARKS:
        s = s.replace(m, " ")
    return s


def fold(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def base_name(raw):
    s = PREFIX.sub("", strip_marks(raw), count=1)
    s = re.sub(r"\s+", " ", re.sub(r"\(\s*\)", " ", QUALITY.sub(" ", s))).strip()
    return re.sub(r"[\s:\-|]+$", "", s).strip()


def epg_key(name):
    s = " " + fold(strip_marks(name)).lower() + " "
    s = QUALITY.sub(" ", s)
    for a, b in ((" m. ", " m+ "), (" movistar+ ", " m+ "), (" movistar plus+ ", " m+ "),
                 (" movistar ", " m+ "), ("factoria de ficcion", "fdf"), (".tv", " ")):
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9+]", "", s)


def clean(s):
    return re.sub(r"\s+", " ", re.sub(r"\[/?COLOR[^\]]*\]", "", s or "")).strip()


def main(channels_path, out_path):
    names = [l.strip() for l in open(channels_path, encoding="utf-8") if l.strip()]
    wanted = {}  # key -> provider names
    for n in names:
        k = epg_key(base_name(n))
        if k:
            wanted.setdefault(k, []).append(n)

    data = urllib.request.urlopen(SRC, timeout=120).read()
    root = ET.fromstring(gzip.decompress(data))
    key_to_xid = {}
    for ch in root.iter("channel"):
        for dn in ch.iter("display-name"):
            k = epg_key(dn.text or "")
            if k and k not in key_to_xid:
                key_to_xid[k] = ch.get("id")
    # provider key -> xmltv id (exact key, or "x 1" -> "x")
    xid_to_names = {}
    for k, ns in wanted.items():
        xid = key_to_xid.get(ALIASES.get(k, k))
        if xid is None and re.search(r"[^0-9]1$", k):
            xid = key_to_xid.get(k[:-1])
        if xid:
            xid_to_names.setdefault(xid, []).extend(ns)

    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<tv generator-info-name="streamvault-epg-es (from davidmuma EPG_dobleM)">']
    for xid, ns in xid_to_names.items():
        for n in ns:
            out.append(f'<channel id="{escape(n, {chr(34): "&quot;"})}"><display-name>{escape(n)}</display-name></channel>')
    progs = 0
    for p in root.iter("programme"):
        ns = xid_to_names.get(p.get("channel"))
        if not ns:
            continue
        titles = {t.get("lang"): clean(t.text) for t in p.iter("title")}
        title = titles.get("en") or titles.get("es") or next(iter(titles.values()), "")
        subs = {t.get("lang"): clean(t.text) for t in p.iter("sub-title")}
        sub = subs.get("en") or subs.get("es") or ""
        desc = next((clean(d.text) for d in p.iter("desc")), "")
        genres = [g.strip() for g in sub.split("|")[0].split(",") if g.strip()] if sub else []
        cats = [label for rx, label in SHOW if rx.search(title)] + genres
        body = f"<title lang=\"es\">{escape(title)}</title>"
        if sub:
            body += f"<sub-title lang=\"es\">{escape(sub)}</sub-title>"
        if desc:
            body += f"<desc lang=\"es\">{escape(desc)}</desc>"
        body += "".join(f"<category lang=\"es\">{escape(c)}</category>" for c in cats[:4])
        attrs = f'start="{p.get("start")}" stop="{p.get("stop")}"'
        for n in ns:
            out.append(f'<programme {attrs} channel="{escape(n, {chr(34): "&quot;"})}">{body}</programme>')
            progs += 1
    out.append("</tv>")
    with gzip.open(out_path, "wt", encoding="utf-8", compresslevel=9) as f:
        f.write("\n".join(out) + "\n")
    mapped = sum(len(v) for v in xid_to_names.values())
    print(f"provider ES channels: {len(names)}, mapped: {mapped} ({len(xid_to_names)} guide channels), programmes: {progs}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
