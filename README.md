# bot-exchange-rate

Scrapes daily foreign exchange rates from the Bank of Thailand and appends
them to a text file, one line per date/currency.

- Source page: https://www.bot.or.th/en/statistics/exchange-rate.html
- Data feed: the JSON endpoint that page calls in the background (no API key needed)

## Requirements

- Python 3.9+ (standard library only, no extra packages to install)

## Usage

```bash
# last 15 days, USD -> thb_rates.txt
python bot_exchange_rate.py

# multiple currencies
python bot_exchange_rate.py --currencies USD EUR JPY

# custom date range
python bot_exchange_rate.py --start 2026-08-01 --end 2026-09-05

# custom output file
python bot_exchange_rate.py --outfile C:\data\rates.txt
```

Each appended line is tab separated:

```
2026-09-04    USD    buying_sight=32.6896    buying_transfer=32.7690    selling=33.0913
```

Lines whose (date, currency) pair is already in the output file are skipped,
so the script is safe to run repeatedly or on a schedule (e.g. cron).

## Options

| Flag | Description | Default |
| --- | --- | --- |
| `--currencies` | One or more currency codes to fetch | `USD` |
| `--start` | Start date (`YYYY-MM-DD`) | 15 days ago |
| `--end` | End date (`YYYY-MM-DD`) | today |
| `--outfile` | Text file to append results to | `thb_rates.txt` |
