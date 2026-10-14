# 🇮🇳 Indian Markets (NSE / BSE) Quantitative Multi-Strategy Interleaved Leaderboard

**Last Automated Run**: Oct 14, 09:41 IST

> **Global Interleaved Ranking**: Evaluated and ordered strictly by quantitative fit score on a **0–10.0 scale** (Minimum Quality Threshold: **Score ≥ 7.0**).

---

## 📈 Part 1: Cash Market (Equity Swing Calls with Entry, Targets & Stop Loss)

| Rank | Symbol | Price | Regime | Score / 10 | Action | Entry | Stop Loss | Target 1 | Target 2 | R:R | Position Status |
| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **#1** | **KOTAKBANK.NS** | ₹442.30 | Bull | **7.8** | 🟢 Buy | ₹441.50 | ₹425.38 | ₹508.64 | ₹552.88 | 6.5x | 🟢 Ongoing (+0.2%) |

---

## ⚡ Part 2: Derivatives Market (Options Spreads, Condors & Futures Leaderboard)

| Rank | Symbol | Price | Market Regime | Score / 10 | Strategy | Structure / Leg Shorthand | Grade |
| :---: | :--- | :--- | :--- | :---: | :--- | :--- | :---: |
| **#1** | **AXISBANK.NS** | ₹1,263.20 | Neutral | **9.6** | Iron Condor | `B1x-Nov-1150PE / S1x-Nov-1200PE / S1x-Nov-1300CE / B1x-Nov-1350CE` | A (Optimal) |
| **#2** | **DRREDDY.NS** | ₹1,220.90 | Neutral | **9.5** | Iron Condor | `B1x-Nov-1000PE / S1x-Nov-1100PE / S1x-Nov-1300CE / B1x-Nov-1400CE` | A (Optimal) |
| **#3** | **TITAN.NS** | ₹4,458.40 | Neutral | **9.0** | Iron Condor | `B1x-Nov-4150PE / S1x-Nov-4250PE / S1x-Nov-4650CE / B1x-Nov-4750CE` | A (Optimal) |
| **#4** | **DIVISLAB.NS** | ₹9,160.50 | Bull | **8.2** | Iron Condor | `B1x-Nov-8600PE / S1x-Nov-8800PE / S1x-Nov-9600CE / B1x-Nov-9800CE` | A (Optimal) |
| **#5** | **SHRIRAMFIN.NS** | ₹967.30 | Bear | **8.0** | Iron Condor | `B1x-Nov-895PE / S1x-Nov-920PE / S1x-Nov-1010CE / B1x-Nov-1035CE` | B (Good) |
| **#6** | **TECHM.NS** | ₹1,545.20 | Bull | **7.7** | Iron Condor | `B1x-Nov-1400PE / S1x-Nov-1450PE / S1x-Nov-1650CE / B1x-Nov-1700CE` | B (Good) |
| **#7** | **BAJAJ-AUTO.NS** | ₹10,322.00 | Bear | **7.5** | Iron Condor | `B1x-Nov-9600PE / S1x-Nov-9800PE / S1x-Nov-11000CE / B1x-Nov-11200CE` | B (Good) |
| **#8** | **GRASIM.NS** | ₹2,894.40 | Bear | **7.2** | Iron Condor | `B1x-Nov-2700PE / S1x-Nov-2750PE / S1x-Nov-3050CE / B1x-Nov-3100CE` | B (Good) |

---

### 🛡️ Execution & Exit Guardrails
- **Cash Swing Exit Rules**: Medium-Term Position (2–6 Months). Target 1 (+15%) triggers partial profit taking & trailing stop loss at EMA20. Target 2 (+25% to 30%) exits full position. Let run as long as trend structure remains intact.
- **Target DTE Window (Derivatives)**: 30–60 DTE Target Expiration Cycle.
- **Take Profit (Derivatives)**: 50% max profit target for Spreads, Ratio Puts & Futures; 25% for Iron Flies & Jade Lizards.
- **21 DTE Review Gate**: Review trade at 21 DTE; close/roll if delta expands past 0.30.
- **14 DTE Mandatory Exit**: Hard exit at 14 DTE to eliminate gamma pin risk.
- **1:1 Stop Loss**: Close position if net loss equals 100% of initial credit collected.
