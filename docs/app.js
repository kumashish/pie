document.addEventListener("DOMContentLoaded", () => {
  const searchForm = document.getElementById("search-form");
  const symbolInput = document.getElementById("symbol-input");
  const analyzeBtn = document.getElementById("analyze-btn");
  const btnSpinner = document.getElementById("btn-spinner");
  
  const loadingState = document.getElementById("loading-state");
  const errorBanner = document.getElementById("error-banner");
  const errorMessage = document.getElementById("error-message");
  const resultsContainer = document.getElementById("results-container");

  // DOM Elements for Results
  const resSymbol = document.getElementById("res-symbol");
  const resPrice = document.getElementById("res-price");
  const resAsOf = document.getElementById("res-as-of");
  const resFitScore = document.getElementById("res-fit-score");
  const resRegime = document.getElementById("res-regime");
  const resConfidence = document.getElementById("res-confidence");

  const resStrategyName = document.getElementById("res-strategy-name");
  const resTradeProfile = document.getElementById("res-trade-profile");
  const resLegsContainer = document.getElementById("res-legs-container");
  const resMaxGain = document.getElementById("res-max-gain");
  const resVix = document.getElementById("res-vix");
  const resExpirationWindow = document.getElementById("res-expiration-window");

  const resIndicatorsGrid = document.getElementById("res-indicators-grid");
  const resRulesTbody = document.getElementById("res-rules-tbody");

  // Quick Chips
  document.querySelectorAll(".chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      const symbol = chip.getAttribute("data-symbol");
      symbolInput.value = symbol;
      fetchAnalysis(symbol);
    });
  });

  // Search Form Submit
  searchForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const symbol = symbolInput.value.trim();
    if (symbol) {
      fetchAnalysis(symbol);
    }
  });

  // Initial Fetch for default symbol SPY
  fetchAnalysis("SPY");

  async function fetchAnalysis(symbol) {
    showLoading();
    const safeSymbol = symbol.replace("^", "").replace(".NS", "_NS").replace(".BO", "_BO").replace(/\s+/g, "_");

    // 1. Try local REST API endpoint first (when running pie serve)
    try {
      const response = await fetch(`/api/analyze?symbol=${encodeURIComponent(symbol)}`);
      if (response.ok) {
        const data = await response.json();
        if (!data.error) {
          renderResults(data);
          hideLoading();
          return;
        }
      }
    } catch (e) {
      // Fall through to static pre-computed JSON
    }

    // 2. Fallback to static pre-computed JSON (when hosted on GitHub Pages)
    try {
      const response = await fetch(`data/${safeSymbol}.json`);
      if (response.ok) {
        const data = await response.json();
        renderResults(data);
        hideLoading();
        return;
      }
      showError(`No pre-computed data available for ${symbol}. Please select a benchmark ticker chip above.`);
    } catch (err) {
      showError(`Failed to load option trade analysis for ${symbol}.`);
    } finally {
      hideLoading();
    }
  }

  function renderResults(data) {
    errorBanner.style.display = "none";
    resultsContainer.style.display = "block";

    // Hero Overview
    resSymbol.textContent = data.symbol;
    const currency = (data.symbol.endsWith(".NS") || data.symbol.endsWith(".BO") || data.symbol.includes("NIFTY") || data.symbol.includes("SENSEX")) ? "₹" : "$";
    resPrice.textContent = `${currency}${data.last_price.toLocaleString()}`;
    resAsOf.textContent = `As of ${data.as_of} IST | Annualized VIX: ${data.vix}%`;

    resFitScore.textContent = (data.fit_score / 10.0).toFixed(1);
    resRegime.textContent = getRegimeBadgeText(data.regime);
    resConfidence.textContent = `Grade ${data.confidence_grade} (${data.confidence_percentage}% Conviction)`;

    // Strategy & Trade Recommendation
    resStrategyName.textContent = data.strategy_display;
    resTradeProfile.textContent = data.trade_profile;
    resMaxGain.textContent = data.estimated_trade ? data.estimated_trade.max_gain : "Defined Risk";
    resVix.textContent = `${data.vix}%`;

    // Render Option Legs
    if (data.estimated_trade && data.estimated_trade.legs && data.estimated_trade.legs.length > 0) {
      resLegsContainer.innerHTML = data.estimated_trade.legs.map((leg) => `
        <div class="leg-card">
          <span class="leg-action ${leg.action.toLowerCase()}">${leg.action.toUpperCase()} ${leg.quantity}x</span>
          <span class="leg-details">${data.symbol} ${leg.strike_formatted} ${leg.option_type}</span>
          <span class="leg-expiry">Expiry: <strong>${leg.expiration_display}</strong> (${leg.dte} DTE)</span>
        </div>
      `).join("");
      resExpirationWindow.textContent = `${data.estimated_trade.legs[0].dte} DTE`;
    } else {
      resLegsContainer.innerHTML = `
        <div class="leg-card">
          <span class="leg-details" style="color: #94a3b8;">No option legs recommended under current market conditions (${data.strategy_display}).</span>
        </div>
      `;
      resExpirationWindow.textContent = "N/A";
    }

    // Render Indicators Grid
    const indEntries = Object.entries(data.indicators);
    if (indEntries.length > 0) {
      resIndicatorsGrid.innerHTML = indEntries.map(([name, val]) => `
        <div class="ind-item">
          <div class="ind-name">${name}</div>
          <div class="ind-value">${val}</div>
        </div>
      `).join("");
    } else {
      resIndicatorsGrid.innerHTML = "<p>No indicators calculated.</p>";
    }

    // Render Rules Table
    if (data.rules && data.rules.length > 0) {
      resRulesTbody.innerHTML = data.rules.map((rule) => `
        <tr>
          <td>
            <span class="status-badge ${rule.passed ? 'pass' : 'fail'}">
              ${rule.passed ? 'PASS' : 'FAIL'}
            </span>
          </td>
          <td><strong>${rule.name}</strong></td>
          <td>${rule.score} / ${rule.max_score}</td>
          <td style="color: #94a3b8;">${rule.explanation}</td>
        </tr>
      `).join("");
    } else {
      resRulesTbody.innerHTML = "<tr><td colspan='4'>No rule evaluations available.</td></tr>";
    }
  }

  function getRegimeBadgeText(regime) {
    const map = {
      "strong_bull": "🟢 Strong Bull",
      "bull": "🟢 Bull",
      "neutral": "🟡 Neutral",
      "bear": "🔴 Bear",
      "strong_bear": "🔴 Strong Bear",
    };
    return map[regime] || `⚪ ${regime}`;
  }

  function showLoading() {
    loadingState.style.display = "block";
    resultsContainer.style.display = "none";
    errorBanner.style.display = "none";
    analyzeBtn.disabled = true;
  }

  function hideLoading() {
    loadingState.style.display = "none";
    analyzeBtn.disabled = false;
  }

  function showError(msg) {
    errorMessage.textContent = msg;
    errorBanner.style.display = "flex";
    resultsContainer.style.display = "none";
  }
});
