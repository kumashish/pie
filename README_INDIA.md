# 🇮🇳 Indian Markets (NSE / BSE) Quantitative Multi-Strategy Interleaved Leaderboard

**Last Automated Run**: Oct 09, 11:58 IST

> **Global Interleaved Ranking**: Evaluated and ordered strictly by quantitative fit score on a **0–10.0 scale** (Minimum Quality Threshold: **Score ≥ 7.0**).

---

## 📈 Part 1: Cash Market (Equity Swing Calls with Entry, Targets & Stop Loss)

| Rank | Symbol | Price | Regime | Score / 10 | Action | Entry | Stop Loss | Target 1 | Target 2 | R:R | Position Status |
| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| - | *No qualifying setups* | - | - | - | - | - | - | - | - | - | *Score threshold < 7.0* |

---

## ⚡ Part 2: Derivatives Market (Options Spreads, Condors & Futures Leaderboard)

| Rank | Symbol | Price | Market Regime | Score / 10 | Strategy | Structure / Leg Shorthand | Grade |
| :---: | :--- | :--- | :--- | :---: | :--- | :--- | :---: |
| **#1** | **DRREDDY.NS** | ₹1,199.80 | Neutral | **8.8** | Iron Condor | `B1x-Nov-1100PE / S1x-Nov-1150PE / S1x-Nov-1250CE / B1x-Nov-1300CE` | A (Optimal) |
| **#2** | **DRREDDY.NS** | ₹1,199.80 | Neutral | **8.4** | Butterfly | `B1x-Nov-1150CE / S2x-Nov-1200CE / B1x-Nov-1250CE` | A (Optimal) |
| **#3** | **BAJFINANCE.NS** | ₹968.90 | Neutral | **8.2** | Iron Condor | `B1x-Nov-895PE / S1x-Nov-920PE / S1x-Nov-1020CE / B1x-Nov-1045CE` | A (Optimal) |
| **#4** | **ADANIENT.NS** | ₹2,797.70 | Neutral | **7.9** | Iron Condor | `B1x-Nov-2600PE / S1x-Nov-2650PE / S1x-Nov-2950CE / B1x-Nov-3000CE` | B (Good) |
| **#5** | **KOTAKBANK.NS** | ₹440.30 | Strong Bull | **7.8** | Credit Spread | `S1x-Nov-420PE / B1x-Nov-410PE` | B (Good) |
| **#6** | **TITAN.NS** | ₹4,374.40 | Neutral | **7.7** | Iron Condor | `B1x-Nov-4050PE / S1x-Nov-4150PE / S1x-Nov-4550CE / B1x-Nov-4650CE` | B (Good) |
| **#7** | **DIVISLAB.NS** | ₹9,620.00 | Strong Bull | **7.6** | Credit Spread | `S1x-Nov-9100PE / B1x-Nov-8900PE` | B (Good) |
| **#8** | **DIVISLAB.NS** | ₹9,620.00 | Strong Bull | **7.5** | Protected Future | `B1x-Nov-9620CE / B1x-Nov-9100PE` | B (Good) |
| **#9** | **DIVISLAB.NS** | ₹9,620.00 | Strong Bull | **7.5** | Poor Mans Covered Call | `B1x-Nov-9100CE / S1x-Nov-9900CE` | B (Good) |
| **#10** | **LT.NS** | ₹3,711.20 | Strong Bear | **7.5** | Credit Spread | `S1x-Nov-3900CE / B1x-Nov-3950CE` | B (Good) |
| **#11** | **KOTAKBANK.NS** | ₹440.30 | Strong Bull | **7.1** | Protected Future | `B1x-Nov-440.3CE / B1x-Nov-420PE` | B (Good) |
| **#12** | **TATASTEEL.NS** | ₹174.88 | Strong Bear | **7.1** | Credit Spread | `S1x-Nov-185CE / B1x-Nov-190CE` | B (Good) |
| **#13** | **EICHERMOT.NS** | ₹7,006.00 | Bear | **7.0** | Credit Spread | `S1x-Nov-7400CE / B1x-Nov-7500CE` | B (Good) |

---

### 🛡️ Execution & Exit Guardrails
- **Cash Swing Exit Rules**: Medium-Term Position (2–6 Months). Target 1 (+15%) triggers partial profit taking & trailing stop loss at EMA20. Target 2 (+25% to 30%) exits full position. Let run as long as trend structure remains intact.
- **Target DTE Window (Derivatives)**: 30–60 DTE Target Expiration Cycle.
- **Take Profit (Derivatives)**: 50% max profit target for Spreads, Ratio Puts & Futures; 25% for Iron Flies & Jade Lizards.
- **21 DTE Review Gate**: Review trade at 21 DTE; close/roll if delta expands past 0.30.
- **14 DTE Mandatory Exit**: Hard exit at 14 DTE to eliminate gamma pin risk.
- **1:1 Stop Loss**: Close position if net loss equals 100% of initial credit collected.
