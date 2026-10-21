# 🇮🇳 Indian Markets (NSE / BSE) Quantitative Multi-Strategy Interleaved Leaderboard

**Last Automated Run**: Oct 21, 22:07 IST

> **Global Interleaved Ranking**: Evaluated and ordered strictly by quantitative fit score on a **0–10.0 scale** (Minimum Quality Threshold: **Score ≥ 7.0** for individual stocks; Benchmark Indices always tracked).

---

## 🌐 Part 1: Macro Benchmark Indices (Always Tracked & Evaluated)

| Symbol | Price | Away from 52W High | Market Regime | Score / 10 | Strategy | Structure / Leg Shorthand | Grade |
| :--- | :--- | :---: | :--- | :---: | :--- | :--- | :---: |
| **NIFTY_FIN_SERVICE.NS** | ₹24,691.45 | `-13.6%` (₹28,562.5) | Strong Bear | **6.3** | Credit Spread | `S1x-Nov-25900CE / B1x-Nov-26200CE` | B (Good) |
| **^BSESN** | ₹73,709.69 | `-14.4%` (₹86,159.0) | Bear | **5.8** | Broken Wing Butterfly | `B1x-Dec-76200CE / S2x-Dec-77100CE / B1x-Dec-78900CE` | C (Moderate) |
| **^NSEI** | ₹22,811.35 | `-13.5%` (₹26,373.2) | Bear | **5.6** | Credit Spread | `S1x-Nov-23600CE / B1x-Nov-23900CE` | C (Moderate) |
| **^NSEMDCP50** | ₹16,500.20 | `-10.8%` (₹18,501.0) | Bear | **5.5** | Broken Wing Butterfly | `B1x-Dec-17100CE / S2x-Dec-17300CE / B1x-Dec-17700CE` | C (Moderate) |
| **^NSEBANK** | ₹54,976.90 | `-11.0%` (₹61,764.8) | Strong Bear | **4.7** | Credit Spread | `S1x-Nov-57600CE / B1x-Nov-58300CE` | C (Moderate) |

---

## 🛡️ Part 1B: NIFTY Income Portfolio Playbook v1.4 — Mean-Reversion Signal Status

| Index | Price | Away from 52W High | 200 SMA Trend Guardrail | Lower BB (20,2σ) | RSI(2) | Signal Status | Diagnosis & Guidance | Proposed Trade (Leg Shorthand) |
| :--- | :--- | :---: | :--- | :--- | :---: | :---: | :--- | :--- |
| **^NSEI** | ₹22,811.35 | `-13.5%` (₹26,373.2) | ❌ Below (Defensive) (₹24,125.0) | ⚪ Inside (₹22,211.8) | `31.1` | 🔴 **STAND ASIDE** | Daily close (22,811.35) is below 200-day SMA (24,124.96). Per Playbook Section 8: Stand aside or remain defensive. Do... | `S1x-Nov-22200PE / B1x-Nov-21900PE` |
| **^NSEBANK** | ₹54,976.90 | `-11.0%` (₹61,764.8) | ❌ Below (Defensive) (₹56,851.8) | ⚪ Inside (₹54,128.6) | `11.7` | 🔴 **STAND ASIDE** | Daily close (54,976.90) is below 200-day SMA (56,851.75). Per Playbook Section 8: Stand aside or remain defensive. Do... | `S1x-Nov-52900PE / B1x-Nov-52200PE` |
| **NIFTY_FIN_SERVICE.NS** | ₹24,691.45 | `-13.6%` (₹28,562.5) | ❌ Below (Defensive) (₹26,120.8) | ✅ Penetrated (₹24,735.4) | `12.2` | 🔴 **STAND ASIDE** | Daily close (24,691.45) is below 200-day SMA (26,120.83). Per Playbook Section 8: Stand aside or remain defensive. Do... | `S1x-Nov-23750PE / B1x-Nov-23450PE` |

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
| **#1** | **SHRIRAMFIN.NS** | ₹956.45 | Bear | **7.8** | Iron Condor | `B1x-Nov-880PE / S1x-Nov-910PE / S1x-Nov-1000CE / B1x-Nov-1030CE` | B (Good) |
| **#2** | **TECHM.NS** | ₹1,554.60 | Bull | **7.6** | Iron Condor | `B1x-Nov-1400PE / S1x-Nov-1450PE / S1x-Nov-1650CE / B1x-Nov-1700CE` | B (Good) |
| **#3** | **BAJAJ-AUTO.NS** | ₹10,312.00 | Bear | **7.4** | Iron Condor | `B1x-Nov-9600PE / S1x-Nov-9800PE / S1x-Nov-11000CE / B1x-Nov-11200CE` | B (Good) |
| **#4** | **DIVISLAB.NS** | ₹9,087.00 | Bull | **7.4** | Iron Condor | `B1x-Nov-8400PE / S1x-Nov-8600PE / S1x-Nov-9400CE / B1x-Nov-9600CE` | B (Good) |
| **#5** | **TITAN.NS** | ₹4,450.20 | Bear | **7.2** | Iron Condor | `B1x-Nov-4150PE / S1x-Nov-4250PE / S1x-Nov-4650CE / B1x-Nov-4750CE` | B (Good) |
| **#6** | **GRASIM.NS** | ₹2,893.60 | Bear | **7.2** | Iron Condor | `B1x-Nov-2700PE / S1x-Nov-2750PE / S1x-Nov-3050CE / B1x-Nov-3100CE` | B (Good) |

---

### 🛡️ Execution & Exit Guardrails
- **Cash Swing Exit Rules**: Medium-Term Position (2–6 Months). Target 1 (+15%) triggers partial profit taking & trailing stop loss at EMA20. Target 2 (+25% to 30%) exits full position. Let run as long as trend structure remains intact.
- **Target DTE Window (Derivatives)**: 30–60 DTE Target Expiration Cycle.
- **Take Profit (Derivatives)**: 50% max profit target for Spreads, Ratio Puts & Futures; 25% for Iron Flies & Jade Lizards.
- **21 DTE Review Gate**: Review trade at 21 DTE; close/roll if delta expands past 0.30.
- **14 DTE Mandatory Exit**: Hard exit at 14 DTE to eliminate gamma pin risk.
- **1:1 Stop Loss**: Close position if net loss equals 100% of initial credit collected.
