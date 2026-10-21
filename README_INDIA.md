# 🇮🇳 Indian Markets (NSE / BSE) Quantitative Multi-Strategy Interleaved Leaderboard

**Last Automated Run**: Oct 21, 09:45 IST

> **Global Interleaved Ranking**: Evaluated and ordered strictly by quantitative fit score on a **0–10.0 scale** (Minimum Quality Threshold: **Score ≥ 7.0** for individual stocks; Benchmark Indices always tracked).

---

## 🌐 Part 1: Macro Benchmark Indices (Always Tracked & Evaluated)

| Symbol | Price | Away from 52W High | Market Regime | Score / 10 | Strategy | Structure / Leg Shorthand | Grade |
| :--- | :--- | :---: | :--- | :---: | :--- | :--- | :---: |
| **^BSESN** | ₹74,550.84 | `-13.5%` (₹86,159.0) | Bear | **7.9** | Iron Condor | `B1x-Nov-70000PE / S1x-Nov-70900PE / S1x-Nov-78300CE / B1x-Nov-79200CE` | B (Good) |
| **^NSEI** | ₹23,100.60 | `-12.4%` (₹26,373.2) | Bear | **7.2** | Iron Condor | `B1x-Nov-22000PE / S1x-Nov-22300PE / S1x-Nov-23900CE / B1x-Nov-24200CE` | B (Good) |
| **NIFTY_FIN_SERVICE.NS** | ₹25,072.90 | `-12.2%` (₹28,562.5) | Strong Bear | **6.0** | Credit Spread | `S1x-Nov-26200CE / B1x-Nov-26450CE` | B (Good) |
| **^NSEMDCP50** | ₹16,750.40 | `-9.5%` (₹18,501.0) | Bear | **4.2** | Iron Condor | `B1x-Nov-15800PE / S1x-Nov-16000PE / S1x-Nov-17500CE / B1x-Nov-17700CE` | C (Moderate) |
| **^NSEBANK** | ₹55,803.25 | `-9.7%` (₹61,764.8) | Bear | **4.1** | Credit Spread | `S1x-Nov-58300CE / B1x-Nov-58900CE` | C (Moderate) |

---

## 🛡️ Part 1B: NIFTY Income Portfolio Playbook v1.4 — Mean-Reversion Signal Status

| Index | Price | Away from 52W High | 200 SMA Trend Guardrail | Lower BB (20,2σ) | RSI(2) | Signal Status | Diagnosis & Guidance | Proposed Trade (Leg Shorthand) |
| :--- | :--- | :---: | :--- | :--- | :---: | :---: | :--- | :--- |
| **^NSEI** | ₹23,100.60 | `-12.4%` (₹26,373.2) | ❌ Below (Defensive) (₹24,126.4) | ⚪ Inside (₹22,197.8) | `69.0` | 🔴 **STAND ASIDE** | Daily close (23,100.60) is below 200-day SMA (24,126.40). Per Playbook Section 8: Stand aside or remain defensive. Do... | `S1x-Nov-22500PE / B1x-Nov-22200PE` |
| **^NSEBANK** | ₹55,803.25 | `-9.7%` (₹61,764.8) | ❌ Below (Defensive) (₹56,855.9) | ⚪ Inside (₹54,113.1) | `67.6` | 🔴 **STAND ASIDE** | Daily close (55,803.25) is below 200-day SMA (56,855.88). Per Playbook Section 8: Stand aside or remain defensive. Do... | `S1x-Nov-53800PE / B1x-Nov-53200PE` |
| **NIFTY_FIN_SERVICE.NS** | ₹25,072.90 | `-12.2%` (₹28,562.5) | ❌ Below (Defensive) (₹26,122.7) | ⚪ Inside (₹24,805.4) | `41.2` | 🔴 **STAND ASIDE** | Daily close (25,072.90) is below 200-day SMA (26,122.74). Per Playbook Section 8: Stand aside or remain defensive. Do... | `S1x-Nov-24150PE / B1x-Nov-23900PE` |

---

## 📈 Part 2: Cash Market (Equity Swing Calls with Entry, Targets & Stop Loss)

| Rank | Symbol | Price | Regime | Score / 10 | Action | Entry | Stop Loss | Target 1 | Target 2 | R:R | Position Status |
| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **#1** | **KOTAKBANK.NS** | ₹443.55 | Bull | **7.8** | 🟢 Buy | ₹441.50 | ₹426.63 | ₹510.08 | ₹554.44 | 6.6x | 🟢 Ongoing (+0.5%) |
| **#2** | **NESTLEIND.NS** | ₹1,370.80 | Bull | **7.0** | 🟢 Buy | ₹1,339.00 | ₹1,331.36 | ₹1,576.42 | ₹1,713.50 | 8.7x | 🟢 Ongoing (+2.4%) |

---

## ⚡ Part 3: Derivatives Market (Options Spreads, Condors & Futures Leaderboard)

| Rank | Symbol | Price | Market Regime | Score / 10 | Strategy | Structure / Leg Shorthand | Grade |
| :---: | :--- | :--- | :--- | :---: | :--- | :--- | :---: |
| **#1** | **^BSESN** | ₹74,550.84 | Bear | **7.9** | Iron Condor | `B1x-Nov-70000PE / S1x-Nov-70900PE / S1x-Nov-78300CE / B1x-Nov-79200CE` | B (Good) |
| **#2** | **SHRIRAMFIN.NS** | ₹956.45 | Bear | **7.8** | Iron Condor | `B1x-Nov-880PE / S1x-Nov-910PE / S1x-Nov-1000CE / B1x-Nov-1030CE` | B (Good) |
| **#3** | **TECHM.NS** | ₹1,554.60 | Bull | **7.6** | Iron Condor | `B1x-Nov-1400PE / S1x-Nov-1450PE / S1x-Nov-1650CE / B1x-Nov-1700CE` | B (Good) |
| **#4** | **BAJAJ-AUTO.NS** | ₹10,312.00 | Bear | **7.4** | Iron Condor | `B1x-Nov-9600PE / S1x-Nov-9800PE / S1x-Nov-11000CE / B1x-Nov-11200CE` | B (Good) |
| **#5** | **DIVISLAB.NS** | ₹9,087.00 | Bull | **7.4** | Iron Condor | `B1x-Nov-8400PE / S1x-Nov-8600PE / S1x-Nov-9400CE / B1x-Nov-9600CE` | B (Good) |
| **#6** | **TITAN.NS** | ₹4,450.20 | Bear | **7.2** | Iron Condor | `B1x-Nov-4150PE / S1x-Nov-4250PE / S1x-Nov-4650CE / B1x-Nov-4750CE` | B (Good) |
| **#7** | **^NSEI** | ₹23,100.60 | Bear | **7.2** | Iron Condor | `B1x-Nov-22000PE / S1x-Nov-22300PE / S1x-Nov-23900CE / B1x-Nov-24200CE` | B (Good) |
| **#8** | **GRASIM.NS** | ₹2,893.60 | Bear | **7.2** | Iron Condor | `B1x-Nov-2700PE / S1x-Nov-2750PE / S1x-Nov-3050CE / B1x-Nov-3100CE` | B (Good) |

---

### 🛡️ Execution & Exit Guardrails
- **Cash Swing Exit Rules**: Medium-Term Position (2–6 Months). Target 1 (+15%) triggers partial profit taking & trailing stop loss at EMA20. Target 2 (+25% to 30%) exits full position. Let run as long as trend structure remains intact.
- **Target DTE Window (Derivatives)**: 30–60 DTE Target Expiration Cycle.
- **Take Profit (Derivatives)**: 50% max profit target for Spreads, Ratio Puts & Futures; 25% for Iron Flies & Jade Lizards.
- **21 DTE Review Gate**: Review trade at 21 DTE; close/roll if delta expands past 0.30.
- **14 DTE Mandatory Exit**: Hard exit at 14 DTE to eliminate gamma pin risk.
- **1:1 Stop Loss**: Close position if net loss equals 100% of initial credit collected.
