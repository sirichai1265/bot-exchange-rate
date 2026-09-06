"""
Scrape daily foreign exchange rates from the Bank of Thailand and append
them to a text file, one line per date/currency.

Source page : https://www.bot.or.th/en/statistics/exchange-rate.html
Data feed   : the JSON endpoint that page calls in the background (no API key).

Usage
-----
    python bot_exchange_rate.py                     # last 15 days, USD, -> thb_rates.txt
    python bot_exchange_rate.py --currencies USD EUR JPY
    python bot_exchange_rate.py --start 2026-08-01 --end 2026-09-05
    python bot_exchange_rate.py --outfile C:\\data\\rates.txt

Each appended line (tab separated):
    2026-09-04    USD    buying_sight=32.6896    buying_transfer=32.7690    selling=33.0913
Lines whose (date, currency) pair is already in the file are skipped, so the
script is safe to run on a schedule.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import urllib.request

BASE_URL = (
    "https://www.bot.or.th/content/bot/en/statistics/exchange-rate/"
    "jcr:content/root/container/"
    "statisticstable1.results.level3cache.daily.{start}.{end}.{currencies}.json"
)

DATE_FMT_API = "%d %b %Y"   # e.g. "04 Sep 2026" (what the feed returns)
DATE_FMT_OUT = "%Y-%m-%d"   # e.g. "2026-09-04" (what we write)


def fetch_rates(start: str, end: str, currencies: list[str]) -> list[dict]:
    """Return the raw rate records from the BoT feed for the given range."""
    url = BASE_URL.format(start=start, end=end, currencies="$".join(currencies))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    return payload.get("responseContent", [])


def load_existing_keys(path: str) -> set[tuple[str, str]]:
    """Read (date, currency) pairs already stored so we don't duplicate them."""
    keys: set[tuple[str, str]] = set()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                parts = line.split("\t")
                if len(parts) >= 2:
                    keys.add((parts[0].strip(), parts[1].strip()))
    except FileNotFoundError:
        pass
    return keys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--currencies", nargs="+", default=["USD"],
                        help="currency codes to fetch (default: USD)")
    parser.add_argument("--start", help="start date YYYY-MM-DD (default: 15 days ago)")
    parser.add_argument("--end", help="end date YYYY-MM-DD (default: today)")
    parser.add_argument("--outfile", default="thb_rates.txt",
                        help="text file to append to (default: thb_rates.txt)")
    args = parser.parse_args(argv)

    today = dt.date.today()
    end = args.end or today.isoformat()
    start = args.start or (today - dt.timedelta(days=15)).isoformat()
    currencies = [c.upper() for c in args.currencies]

    try:
        records = fetch_rates(start, end, currencies)
    except Exception as exc:  # network / JSON errors
        print(f"ERROR: could not fetch rates: {exc}", file=sys.stderr)
        return 1

    if not records:
        print("No rate data returned for the requested range.")
        return 0

    existing = load_existing_keys(args.outfile)
    new_rows: list[tuple[str, str, str]] = []

    for rec in records:
        currency = rec.get("currency_id", "").strip()
        try:
            date_out = dt.datetime.strptime(rec["period"].strip(),
                                            DATE_FMT_API).strftime(DATE_FMT_OUT)
        except (KeyError, ValueError):
            continue
        if (date_out, currency) in existing:
            continue
        line = (
            f"{date_out}\t{currency}\t"
            f"buying_sight={rec.get('buying_sight', '')}\t"
            f"buying_transfer={rec.get('buying_transfer', '')}\t"
            f"selling={rec.get('selling', '')}"
        )
        new_rows.append((date_out, currency, line))
        existing.add((date_out, currency))

    if not new_rows:
        print("Already up to date - nothing new to append.")
        return 0

    new_rows.sort(key=lambda r: (r[0], r[1]))
    with open(args.outfile, "a", encoding="utf-8") as fh:
        for _, _, line in new_rows:
            fh.write(line + "\n")

    print(f"Appended {len(new_rows)} line(s) to {args.outfile}:")
    for _, _, line in new_rows:
        print("  " + line.replace("\t", " | "))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
