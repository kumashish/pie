# 🇮🇳 Indian Markets (NSE / BSE) Quantitative Multi-Strategy Interleaved Leaderboard

**Last Automated Run**: Oct 15, 11:23 IST

> **Global Interleaved Ranking**: Evaluated and ordered strictly by quantitative fit score on a **0–10.0 scale** (Minimum Quality Threshold: **Score ≥ 7.0** for individual stocks; Benchmark Indices always tracked).

---

## 🌐 Part 1: Macro Benchmark Indices (Always Tracked & Evaluated)

| Symbol | Price | Market Regime | Score / 10 | Strategy | Structure / Leg Shorthand | Grade |
| :--- | :--- | :--- | :---: | :--- | :--- | :---: |
| **^BSESN** | ₹73,841.13 | Bear | **6.7** | Iron Condor | `B1x-Nov-69000PE / S1x-Nov-69900PE / S1x-Nov-77700CE / B1x-Nov-78600CE` | B (Good) |
| **NIFTY_FIN_SERVICE.NS** | ₹25,201.90 | Bear | **6.7** | Iron Condor | `B1x-Nov-23700PE / S1x-Nov-23950PE / S1x-Nov-26450CE / B1x-Nov-26700CE` | B (Good) |
| **^NSEI** | ₹22,920.75 | Bear | **5.7** | Credit Spread | `S1x-Nov-23700CE / B1x-Nov-24000CE` | C (Moderate) |
| **^NSEMDCP50** | ₹17,018.95 | Bear | **5.0** | Iron Condor | `B1x-Nov-15950PE / S1x-Nov-16150PE / S1x-Nov-17850CE / B1x-Nov-18050CE` | C (Moderate) |
| **^NSEBANK** | ₹55,720.05 | Bear | **4.3** | Credit Spread | `S1x-Nov-58400CE / B1x-Nov-59000CE` | C (Moderate) |

---

## 🛡️ Part 1B: NIFTY Income Portfolio Playbook v1.4 — Mean-Reversion Signal Status

| Index | Price | 200 SMA Trend Guardrail | Lower BB (20,2σ) | RSI(2) | Signal Status | Diagnosis & Guidance | Proposed Structure |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| **^NSEI** | ₹22,920.75 | ❌ Below (Defensive) (₹24,170.0) | ⚪ Inside (₹22,084.7) | `82.9` | 🔴 **STAND ASIDE** | Daily close (22,920.75) is below 200-day SMA (24,169.96). Per Playbook Section 8: Stand aside or remain defensive. Do... | `Sell 1x OTM Put (~0.25-0.30 Delta) + Buy 1x OTM Put (Defined Risk Wing 1:1, Never Naked)` |
| **^NSEBANK** | ₹55,720.05 | ❌ Below (Defensive) (₹56,905.3) | ⚪ Inside (₹53,875.4) | `80.6` | 🔴 **STAND ASIDE** | Daily close (55,720.05) is below 200-day SMA (56,905.33). Per Playbook Section 8: Stand aside or remain defensive. Do... | `Sell 1x OTM Put (~0.25-0.30 Delta) + Buy 1x OTM Put (Defined Risk Wing 1:1, Never Naked)` |
| **NIFTY_FIN_SERVICE.NS** | ₹25,201.90 | ❌ Below (Defensive) (₹26,169.7) | ⚪ Inside (₹24,811.3) | `73.7` | 🔴 **STAND ASIDE** | Daily close (25,201.90) is below 200-day SMA (26,169.70). Per Playbook Section 8: Stand aside or remain defensive. Do... | `Sell 1x OTM Put (~0.25-0.30 Delta) + Buy 1x OTM Put (Defined Risk Wing 1:1, Never Naked)` |

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
