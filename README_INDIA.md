# 🇮🇳 Indian Markets (NSE / BSE) Quantitative Multi-Strategy Interleaved Leaderboard

**Last Automated Run**: Oct 14, 23:22 IST

> **Global Interleaved Ranking**: Evaluated and ordered strictly by quantitative fit score on a **0–10.0 scale** (Minimum Quality Threshold: **Score ≥ 7.0** for individual stocks; Benchmark Indices always tracked).

---

## 🌐 Part 1: Macro Benchmark Indices (Always Tracked & Evaluated)

| Symbol | Price | Market Regime | Score / 10 | Strategy | Structure / Leg Shorthand | Grade |
| :--- | :--- | :--- | :---: | :--- | :--- | :---: |
| **NIFTY_FIN_SERVICE.NS** | ₹24,948.70 | Strong Bear | **6.4** | Credit Spread | `S1x-Nov-26150CE / B1x-Nov-26400CE` | B (Good) |
| **^BSESN** | ₹72,781.89 | Bear | **5.9** | Iron Condor | `B1x-Nov-68100PE / S1x-Nov-68900PE / S1x-Nov-76700CE / B1x-Nov-77500CE` | C (Moderate) |
| **^NSEI** | ₹22,622.70 | Bear | **5.9** | Credit Spread | `S1x-Nov-23400CE / B1x-Nov-23600CE` | C (Moderate) |
| **^NSEMDCP50** | ₹16,997.35 | Bear | **4.9** | Iron Condor | `B1x-Nov-15950PE / S1x-Nov-16150PE / S1x-Nov-17850CE / B1x-Nov-18050CE` | C (Moderate) |
| **^NSEBANK** | ₹55,316.00 | Strong Bear | **4.5** | Credit Spread | `S1x-Nov-58000CE / B1x-Nov-58600CE` | C (Moderate) |

---

## 🛡️ Part 1B: NIFTY Income Portfolio Playbook v1.4 — Mean-Reversion Signal Status

| Index | Price | 200 SMA Trend Guardrail | Lower BB (20,2σ) | RSI(2) | Signal Status | Diagnosis & Guidance | Proposed Structure |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| **^NSEI** | ₹22,622.70 | ❌ Below (Defensive) (₹24,186.1) | ⚪ Inside (₹22,061.8) | `56.6` | 🔴 **STAND ASIDE** | Daily close (22,622.70) is below 200-day SMA (24,186.06). Per Playbook Section 8: Stand aside or remain defensive. Do... | `Sell 1x OTM Put (~0.25-0.30 Delta) + Buy 1x OTM Put (Defined Risk Wing 1:1, Never Naked)` |
| **^NSEBANK** | ₹55,316.00 | ❌ Below (Defensive) (₹56,922.6) | ⚪ Inside (₹53,826.1) | `57.0` | 🔴 **STAND ASIDE** | Daily close (55,316.00) is below 200-day SMA (56,922.64). Per Playbook Section 8: Stand aside or remain defensive. Do... | `Sell 1x OTM Put (~0.25-0.30 Delta) + Buy 1x OTM Put (Defined Risk Wing 1:1, Never Naked)` |
| **NIFTY_FIN_SERVICE.NS** | ₹24,948.70 | ❌ Below (Defensive) (₹26,183.1) | ⚪ Inside (₹24,814.9) | `5.8` | 🔴 **STAND ASIDE** | Daily close (24,948.70) is below 200-day SMA (26,183.10). Per Playbook Section 8: Stand aside or remain defensive. Do... | `Sell 1x OTM Put (~0.25-0.30 Delta) + Buy 1x OTM Put (Defined Risk Wing 1:1, Never Naked)` |

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
| **#1** | **AXISBANK.NS** | ₹1,269.50 | Neutral | **9.6** | Iron Condor | `B1x-Nov-1150PE / S1x-Nov-1200PE / S1x-Nov-1300CE / B1x-Nov-1350CE` | A (Optimal) |
| **#2** | **DRREDDY.NS** | ₹1,217.50 | Neutral | **9.6** | Iron Condor | `B1x-Nov-1000PE / S1x-Nov-1100PE / S1x-Nov-1300CE / B1x-Nov-1400CE` | A (Optimal) |
| **#3** | **DIVISLAB.NS** | ₹9,090.00 | Bull | **8.2** | Iron Condor | `B1x-Nov-8400PE / S1x-Nov-8600PE / S1x-Nov-9400CE / B1x-Nov-9600CE` | A (Optimal) |
| **#4** | **SHRIRAMFIN.NS** | ₹956.45 | Bear | **7.8** | Iron Condor | `B1x-Nov-880PE / S1x-Nov-910PE / S1x-Nov-1000CE / B1x-Nov-1030CE` | B (Good) |
| **#5** | **TECHM.NS** | ₹1,554.60 | Bull | **7.6** | Iron Condor | `B1x-Nov-1400PE / S1x-Nov-1450PE / S1x-Nov-1650CE / B1x-Nov-1700CE` | B (Good) |
| **#6** | **BAJAJ-AUTO.NS** | ₹10,312.00 | Bear | **7.4** | Iron Condor | `B1x-Nov-9600PE / S1x-Nov-9800PE / S1x-Nov-11000CE / B1x-Nov-11200CE` | B (Good) |
| **#7** | **TITAN.NS** | ₹4,450.20 | Bear | **7.2** | Iron Condor | `B1x-Nov-4150PE / S1x-Nov-4250PE / S1x-Nov-4650CE / B1x-Nov-4750CE` | B (Good) |
| **#8** | **GRASIM.NS** | ₹2,893.60 | Bear | **7.2** | Iron Condor | `B1x-Nov-2700PE / S1x-Nov-2750PE / S1x-Nov-3050CE / B1x-Nov-3100CE` | B (Good) |

---

### 🛡️ Execution & Exit Guardrails
- **Cash Swing Exit Rules**: Medium-Term Position (2–6 Months). Target 1 (+15%) triggers partial profit taking & trailing stop loss at EMA20. Target 2 (+25% to 30%) exits full position. Let run as long as trend structure remains intact.
- **Target DTE Window (Derivatives)**: 30–60 DTE Target Expiration Cycle.
- **Take Profit (Derivatives)**: 50% max profit target for Spreads, Ratio Puts & Futures; 25% for Iron Flies & Jade Lizards.
- **21 DTE Review Gate**: Review trade at 21 DTE; close/roll if delta expands past 0.30.
- **14 DTE Mandatory Exit**: Hard exit at 14 DTE to eliminate gamma pin risk.
- **1:1 Stop Loss**: Close position if net loss equals 100% of initial credit collected.
