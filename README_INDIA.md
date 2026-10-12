# 🇮🇳 Indian Markets (NSE / BSE) Quantitative Multi-Strategy Interleaved Leaderboard

**Last Automated Run**: Oct 12, 13:57 IST

> **Global Interleaved Ranking**: Evaluated and ordered strictly by quantitative fit score on a **0–10.0 scale** (Minimum Quality Threshold: **Score ≥ 7.0**).

---

## 📈 Part 1: Cash Market (Equity Swing Calls with Entry, Targets & Stop Loss)

| Rank | Symbol | Price | Regime | Score / 10 | Action | Entry | Stop Loss | Target 1 | Target 2 | R:R | Position Status |
| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **#1** | **ADANIPORTS.NS** | ₹1,758.70 | Strong Bull | **8.2** | 🟢 Buy | ₹1,758.70 | ₹1,730.39 | ₹2,022.50 | ₹2,198.38 | 15.5x | 🟢 Ongoing (0.0%) |
| **#2** | **KOTAKBANK.NS** | ₹441.50 | Bull | **7.5** | 🟢 Buy | ₹441.50 | ₹423.89 | ₹507.72 | ₹551.88 | 6.3x | 🟢 Ongoing (0.0%) |
| **#3** | **DIVISLAB.NS** | ₹9,343.50 | Bull | **7.5** | 🟢 Buy | ₹9,343.50 | ₹8,974.70 | ₹10,745.02 | ₹11,679.38 | 6.3x | 🟢 Ongoing (0.0%) |

---

## ⚡ Part 2: Derivatives Market (Options Spreads, Condors & Futures Leaderboard)

| Rank | Symbol | Price | Market Regime | Score / 10 | Strategy | Structure / Leg Shorthand | Grade |
| :---: | :--- | :--- | :--- | :---: | :--- | :--- | :---: |
| **#1** | **TATASTEEL.NS** | ₹176.20 | Strong Bear | **8.6** | Credit Spread | `S1x-Nov-185CE / B1x-Nov-190CE` | A (Optimal) |
| **#2** | **DRREDDY.NS** | ₹1,214.60 | Neutral | **8.6** | Iron Condor | `B1x-Nov-1000PE / S1x-Nov-1100PE / S1x-Nov-1300CE / B1x-Nov-1400CE` | A (Optimal) |
| **#3** | **LT.NS** | ₹3,697.70 | Strong Bear | **8.4** | Credit Spread | `S1x-Nov-3900CE / B1x-Nov-3950CE` | A (Optimal) |
| **#4** | **HINDALCO.NS** | ₹903.40 | Bear | **8.3** | Credit Spread | `S1x-Nov-950CE / B1x-Nov-970CE` | A (Optimal) |
| **#5** | **GRASIM.NS** | ₹2,898.40 | Bear | **7.8** | Credit Spread | `S1x-Nov-3050CE / B1x-Nov-3100CE` | B (Good) |
| **#6** | **CIPLA.NS** | ₹1,310.80 | Strong Bear | **7.8** | Credit Spread | `S1x-Nov-1350CE / B1x-Nov-1400CE` | B (Good) |
| **#7** | **ITC.NS** | ₹262.20 | Strong Bear | **7.7** | Credit Spread | `S1x-Nov-275CE / B1x-Nov-280CE` | B (Good) |
| **#8** | **SBIN.NS** | ₹947.85 | Bear | **7.7** | Credit Spread | `S1x-Nov-1000CE / B1x-Nov-1015CE` | B (Good) |
| **#9** | **DIVISLAB.NS** | ₹9,343.50 | Bull | **7.7** | Credit Spread | `S1x-Nov-9000PE / B1x-Nov-8800PE` | B (Good) |
| **#10** | **ADANIENT.NS** | ₹2,640.00 | Bear | **7.5** | Credit Spread | `S1x-Nov-2800CE / B1x-Nov-2900CE` | B (Good) |
| **#11** | **DRREDDY.NS** | ₹1,214.60 | Neutral | **7.5** | Butterfly | `B1x-Nov-1200CE / S2x-Nov-1200CE / B1x-Nov-1200CE` | B (Good) |
| **#12** | **TECHM.NS** | ₹1,458.10 | Bear | **7.5** | Credit Spread | `S1x-Nov-1550CE / B1x-Nov-1600CE` | B (Good) |
| **#13** | **POWERGRID.NS** | ₹250.40 | Strong Bear | **7.4** | Credit Spread | `S1x-Nov-265CE / B1x-Nov-270CE` | B (Good) |
| **#14** | **SUNPHARMA.NS** | ₹1,761.40 | Bear | **7.3** | Credit Spread | `S1x-Nov-1850CE / B1x-Nov-1900CE` | B (Good) |
| **#15** | **SBILIFE.NS** | ₹1,685.00 | Strong Bear | **7.3** | Credit Spread | `S1x-Nov-1800CE / B1x-Nov-1850CE` | B (Good) |
| **#16** | **NIFTY_FIN_SERVICE.NS** | ₹24,953.95 | Strong Bear | **7.1** | Credit Spread | `S1x-Nov-26250CE / B1x-Nov-26550CE` | B (Good) |
| **#17** | **NTPC.NS** | ₹310.30 | Strong Bear | **7.0** | Credit Spread | `S1x-Nov-325CE / B1x-Nov-330CE` | B (Good) |

---

### 🛡️ Execution & Exit Guardrails
- **Cash Swing Exit Rules**: Medium-Term Position (2–6 Months). Target 1 (+15%) triggers partial profit taking & trailing stop loss at EMA20. Target 2 (+25% to 30%) exits full position. Let run as long as trend structure remains intact.
- **Target DTE Window (Derivatives)**: 30–60 DTE Target Expiration Cycle.
- **Take Profit (Derivatives)**: 50% max profit target for Spreads, Ratio Puts & Futures; 25% for Iron Flies & Jade Lizards.
- **21 DTE Review Gate**: Review trade at 21 DTE; close/roll if delta expands past 0.30.
- **14 DTE Mandatory Exit**: Hard exit at 14 DTE to eliminate gamma pin risk.
- **1:1 Stop Loss**: Close position if net loss equals 100% of initial credit collected.
