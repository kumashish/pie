<!-- MARKET-SNAPSHOT-START -->
| Market    | Updated   | Trend      | Strategy          | Signal | Since          |
| --------- | --------- | ---------- | ----------------- | ------ | -------------- |
| NIFTY 50  | 15:31 IST | 🔴 Bear     | Buy NIFTY 25-Aug-2026-23750-PE<br>Sell NIFTY 25-Aug-2026-23000-PE | Active | Today, 11:27   |
| BANKNIFTY | 15:31 IST | 🟢 Strong Bull | Buy BANKNIFTY 25-Aug-2026-56700-CE<br>Sell BANKNIFTY 25-Aug-2026-59000-CE | NEW    | Today, 15:31   |
| SPY       | 22:33 IST | 🟢 Strong Bull | Buy SPY 25-Aug-2026-741-CE<br>Sell SPY 25-Aug-2026-770-CE | NEW    | Today, 22:33   |
| QQQ       | 22:33 IST | 🟢 Bull     | Buy QQQ 25-Aug-2026-689-CE<br>Sell QQQ 25-Aug-2026-716-CE | Active | Today, 12:31   |
| HDFCBANK.NS | 15:31 IST | 🔴 Strong Bear | Buy HDFCBANK.NS 25-Aug-2026-743-PE<br>Sell HDFCBANK.NS 25-Aug-2026-712-PE | Active | Today, 13:27   |
| ICICIBANK.NS | 15:31 IST | 🟢 Strong Bull | Buy ICICIBANK.NS 25-Aug-2026-1430-CE<br>Sell ICICIBANK.NS 25-Aug-2026-1490-CE | Active | Today, 13:27   |
| INFY.NS   | 15:31 IST | 🔴 Strong Bear | Buy INFY.NS 25-Aug-2026-1041-PE<br>Sell INFY.NS 25-Aug-2026-998-PE | Active | Today, 13:27   |
| SBIN.NS   | 15:31 IST | 🟢 Strong Bull | Buy SBIN.NS 25-Aug-2026-1015-CE<br>Sell SBIN.NS 25-Aug-2026-1057-CE | NEW    | Today, 15:31   |
| TCS.NS    | 15:31 IST | 🔴 Bear     | Buy TCS.NS 25-Aug-2026-2254-PE<br>Sell TCS.NS 25-Aug-2026-2161-PE | Active | Today, 13:27   |
| WIPRO.NS  | 15:31 IST | 🔴 Strong Bear | Buy WIPRO.NS 25-Aug-2026-177-PE<br>Sell WIPRO.NS 25-Aug-2026-170-PE | Active | Today, 13:27   |
<!-- MARKET-SNAPSHOT-END -->

![Build](https://img.shields.io/badge/build-passing-brightgreen)
![Python](https://img.shields.io/badge/python-3.12-blue)
# Portfolio Intelligence

A personal market and options decision engine for systematic premium selling, directional overlays, and adaptive learning.

## What this does

- Scans market regime indicators
- Scores portfolio risk and exposure
- Suggests exactly one highest-expected-value trade
- Learns from outcomes over time

## Core idea

The engine treats your portfolio as a two-sided premium-selling book:
- short calls
- short puts
- optional directional hedges

It aims to improve the whole portfolio, not just a single position.

## Planned structure

- `config/` — scoring weights and risk limits
- `engine/` — indicator, portfolio, and trade selection logic
- `portfolio/` — position snapshots and buying power state
- `recommendations/` — daily recommendation outputs
- `outcomes/` — executed trade results and learning data
- `reports/` — daily and weekly reports
- `docs/` — design notes and operating rules

## Status

Initial scaffold.

## Backtesting

Run a reproducible local NIFTY backtest with the included OHLCV dataset:

```bash
uv run pie backtest-market ^NSEI --data-path data/market/nifty50_25years_ohlcv_1999_2026.csv
```

The report evaluates directional trend signals against index returns; it does not model option-spread pricing.
