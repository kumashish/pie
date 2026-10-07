# 🇮🇳 Indian Markets (NSE / BSE) Quantitative Trade Dashboard

**Last Automated Run**: Oct 07, 10:34 IST

---

### 🏆 Top Quantitative Indian Trade Recommendations

| Symbol | Price | Market Regime | Score | Strategy | Structure / Leg Shorthand |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **DIVISLAB.NS** | ₹9,509.00 | Strong Bull | **8.8/10** | Credit Spread | `S1x-Nov-9000PE-B1x-Nov-8800PE` |
| **KOTAKBANK.NS** | ₹439.45 | Bull | **7.8/10** | Credit Spread | `S1x-Nov-420PE-B1x-Nov-410PE` |
| **ADANIPORTS.NS** | ₹1,775.30 | Bull | **7.2/10** | Credit Spread | `S1x-Nov-1700PE-B1x-Nov-1650PE` |
| **TITAN.NS** | ₹4,385.70 | Neutral | **4.2/10** | Credit Spread | `S1x-Nov-4600CE-B1x-Nov-4700CE` |
| **JSWSTEEL.NS** | ₹1,241.00 | Neutral | **4.2/10** | Iron Condor | `B1x-Nov-1150PE-S1x-Nov-1200PE-S1x-Nov-1300CE-B1x-Nov-1350CE` |
| **DRREDDY.NS** | ₹1,216.20 | Neutral | **4.2/10** | Iron Condor | `B1x-Nov-1100PE-S1x-Nov-1150PE-S1x-Nov-1250CE-B1x-Nov-1300CE` |
| **ADANIENT.NS** | ₹2,831.10 | Neutral | **4.0/10** | Iron Condor | `B1x-Nov-2650PE-S1x-Nov-2700PE-S1x-Nov-3000CE-B1x-Nov-3050CE` |
| **BAJAJ-AUTO.NS** | ₹9,839.00 | Bear | **3.5/10** | Credit Spread | `S1x-Nov-10300CE-B1x-Nov-10500CE` |
| **HEROMOTOCO.NS** | ₹5,016.00 | Bear | **3.5/10** | Credit Spread | `S1x-Nov-5200CE-B1x-Nov-5300CE` |
| **TRENT.NS** | ₹2,890.00 | Bear | **3.5/10** | Credit Spread | `S1x-Nov-3050CE-B1x-Nov-3150CE` |
| **^NSEMDCP50** | ₹17,058.35 | Bear | **3.2/10** | Credit Spread | `S1x-Nov-17900CE-B1x-Nov-18100CE` |
| **BAJFINANCE.NS** | ₹969.65 | Bear | **3.2/10** | Credit Spread | `S1x-Nov-1020CE-B1x-Nov-1040CE` |
| **NESTLEIND.NS** | ₹1,331.30 | Bear | **3.2/10** | Credit Spread | `S1x-Nov-1400CE-B1x-Nov-1450CE` |
| **APOLLOHOSP.NS** | ₹7,887.00 | Bear | **3.2/10** | Credit Spread | `S1x-Nov-8300CE-B1x-Nov-8500CE` |
| **AXISBANK.NS** | ₹1,256.00 | Bear | **3.0/10** | Credit Spread | `S1x-Nov-1300CE-B1x-Nov-1350CE` |
| **GRASIM.NS** | ₹2,943.90 | Bear | **3.0/10** | Credit Spread | `S1x-Nov-3100CE-B1x-Nov-3150CE` |
| **EICHERMOT.NS** | ₹7,034.00 | Bear | **3.0/10** | Credit Spread | `S1x-Nov-7300CE-B1x-Nov-7400CE` |
| **SHRIRAMFIN.NS** | ₹952.55 | Bear | **3.0/10** | Credit Spread | `S1x-Nov-1000CE-B1x-Nov-1020CE` |
| **ICICIBANK.NS** | ₹1,348.00 | Bear | **2.5/10** | Credit Spread | `S1x-Nov-1400CE-B1x-Nov-1450CE` |
| **SUNPHARMA.NS** | ₹1,788.30 | Bear | **2.5/10** | Credit Spread | `S1x-Nov-1900CE-B1x-Nov-1950CE` |
| **HINDALCO.NS** | ₹921.30 | Bear | **2.5/10** | Credit Spread | `S1x-Nov-965CE-B1x-Nov-985CE` |
| **HDFCLIFE.NS** | ₹542.20 | Bear | **2.5/10** | Credit Spread | `S1x-Nov-565CE-B1x-Nov-580CE` |
| **^NSEI** | ₹22,687.65 | Bear | **2.2/10** | Credit Spread | `S1x-Nov-23800CE-B1x-Nov-24000CE` |
| **^BSESN** | ₹72,773.10 | Bear | **2.2/10** | Credit Spread | `S1x-Nov-76600CE-B1x-Nov-77300CE` |
| **ITC.NS** | ₹266.15 | Bear | **2.2/10** | Credit Spread | `S1x-Nov-280CE-B1x-Nov-285CE` |

---

### 🛡️ Execution & Exit Guardrails
- **Target DTE Window**: 30–60 DTE Target Expiration Cycle.
- **Take Profit**: 50% max profit target for Spreads & Futures; 25% for Iron Flies & Jade Lizards.
- **21 DTE Review Gate**: Review trade at 21 DTE; close/roll if delta expands past 0.30.
- **14 DTE Mandatory Exit**: Hard exit at 14 DTE to eliminate gamma pin risk.
- **1:1 Stop Loss**: Close position if net loss equals 100% of initial credit collected.
