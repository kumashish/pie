# 🇺🇸 U.S. Markets (NYSE / NASDAQ) Quantitative Trade Dashboard

**Last Automated Run**: Oct 07, 10:34 IST

---

### 🏆 Top Quantitative U.S. Trade Recommendations

| Symbol | Price | Market Regime | Score | Strategy | Structure / Leg Shorthand |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **META** | $738.88 | Strong Bull | **8.8/10** | Credit Spread | `Sell 1x META 20-Nov-2026 700 Put /  Buy 1x META 20-Nov-2026 675 Put` |
| **AMD** | $649.42 | Strong Bull | **8.0/10** | Credit Spread | `Sell 1x AMD 20-Nov-2026 615 Put /  Buy 1x AMD 20-Nov-2026 590 Put` |
| **AMAT** | $530.27 | Strong Bull | **8.0/10** | Credit Spread | `Sell 1x AMAT 20-Nov-2026 500 Put /  Buy 1x AMAT 20-Nov-2026 480 Put` |
| **VTI** | $382.54 | Bull | **7.8/10** | Credit Spread | `Sell 1x VTI 20-Nov-2026 365 Put /  Buy 1x VTI 20-Nov-2026 360 Put` |
| **VOO** | $716.20 | Bull | **7.8/10** | Credit Spread | `Sell 1x VOO 20-Nov-2026 680 Put /  Buy 1x VOO 20-Nov-2026 675 Put` |
| **MSFT** | $529.30 | Bull | **7.8/10** | Credit Spread | `Sell 1x MSFT 20-Nov-2026 500 Put /  Buy 1x MSFT 20-Nov-2026 490 Put` |
| **PLTR** | $192.07 | Bull | **7.8/10** | Credit Spread | `Sell 1x PLTR 20-Nov-2026 180 Put /  Buy 1x PLTR 20-Nov-2026 175 Put` |
| **SMCI** | $43.46 | Bull | **7.8/10** | Credit Spread | `Sell 1x SMCI 20-Nov-2026 40 Put /  Buy 1x SMCI 20-Nov-2026 38 Put` |
| **MU** | $1,045.56 | Bull | **7.8/10** | Credit Spread | `Sell 1x MU 20-Nov-2026 1000 Put /  Buy 1x MU 20-Nov-2026 950 Put` |
| **V** | $370.64 | Bull | **7.8/10** | Credit Spread | `Sell 1x V 20-Nov-2026 350 Put /  Buy 1x V 20-Nov-2026 345 Put` |
| **XOM** | $164.48 | Bull | **7.8/10** | Credit Spread | `Sell 1x XOM 20-Nov-2026 155 Put /  Buy 1x XOM 20-Nov-2026 150 Put` |
| **INTC** | $112.50 | Bull | **7.5/10** | Credit Spread | `Sell 1x INTC 20-Nov-2026 100 Put /  Buy 1x INTC 20-Nov-2026 95 Put` |
| **ARM** | $302.56 | Bull | **7.5/10** | Credit Spread | `Sell 1x ARM 20-Nov-2026 280 Put /  Buy 1x ARM 20-Nov-2026 260 Put` |
| **SPY** | $779.09 | Bull | **7.2/10** | Credit Spread | `Sell 1x SPY 20-Nov-2026 740 Put /  Buy 1x SPY 20-Nov-2026 725 Put` |
| **AAPL** | $333.63 | Bull | **7.2/10** | Credit Spread | `Sell 1x AAPL 20-Nov-2026 320 Put /  Buy 1x AAPL 20-Nov-2026 315 Put` |
| **XLE** | $63.75 | Bull | **7.0/10** | Credit Spread | `Sell 1x XLE 20-Nov-2026 61 Put /  Buy 1x XLE 20-Nov-2026 60 Put` |
| **AVGO** | $375.81 | Bull | **7.0/10** | Credit Spread | `Sell 1x AVGO 20-Nov-2026 395 Call /  Buy 1x AVGO 20-Nov-2026 405 Call` |
| **MA** | $566.58 | Bull | **7.0/10** | Credit Spread | `Sell 1x MA 20-Nov-2026 535 Put /  Buy 1x MA 20-Nov-2026 525 Put` |
| **QQQ** | $759.66 | Bull | **6.8/10** | Credit Spread | `Sell 1x QQQ 20-Nov-2026 720 Put /  Buy 1x QQQ 20-Nov-2026 710 Put` |
| **XLK** | $202.00 | Bull | **6.8/10** | Credit Spread | `Sell 1x XLK 20-Nov-2026 190 Put /  Buy 1x XLK 20-Nov-2026 185 Put` |
| **SOXX** | $589.45 | Bull | **6.8/10** | Credit Spread | `Sell 1x SOXX 20-Nov-2026 560 Put /  Buy 1x SOXX 20-Nov-2026 545 Put` |
| **NVDA** | $239.24 | Bull | **6.8/10** | Credit Spread | `Sell 1x NVDA 20-Nov-2026 230 Put /  Buy 1x NVDA 20-Nov-2026 225 Put` |
| **AMZN** | $256.29 | Bull | **6.8/10** | Credit Spread | `Sell 1x AMZN 20-Nov-2026 270 Call /  Buy 1x AMZN 20-Nov-2026 275 Call` |
| **SOXL** | $164.26 | Bull | **6.8/10** | Credit Spread | `Sell 1x SOXL 20-Nov-2026 150 Put /  Buy 1x SOXL 20-Nov-2026 140 Put` |
| **GOOGL** | $347.68 | Bull | **6.2/10** | Iron Condor | `Buy 1x GOOGL 20-Nov-2026 320 Put /  Sell 1x GOOGL 20-Nov-2026 330 Put /  Sell 1x GOOGL 20-Nov-2026 370 Call /  Buy 1x GOOGL 20-Nov-2026 380 Call` |

---

### 🛡️ Execution & Exit Guardrails
- **Target DTE Window**: 30–60 DTE Target Expiration Cycle.
- **Take Profit**: 50% max profit target for Spreads & Futures; 25% for Iron Flies & Jade Lizards.
- **21 DTE Review Gate**: Review trade at 21 DTE; close/roll if delta expands past 0.30.
- **14 DTE Mandatory Exit**: Hard exit at 14 DTE to eliminate gamma pin risk.
- **1:1 Stop Loss**: Close position if net loss equals 100% of initial credit collected.
