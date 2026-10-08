"""Hidden Markov Model (HMM) Market Regime & Transition State Detector."""

import numpy as np
import polars as pl
import logging

logger = logging.getLogger(__name__)


def calculate_hmm_regime(df: pl.DataFrame, n_states: int = 3) -> dict[str, float]:
    """Fit a 3-State Gaussian Hidden Markov Model to daily log-returns and realized volatility.
    
    Identifies hidden regime states:
    - State 0: Low Volatility Bullish Regime
    - State 1: High Volatility Bearish/Panic Regime
    - State 2: Neutral / Squeeze Regime
    
    Returns 5-session forward transition state probabilities.
    """
    if "close" not in df.columns or len(df) < 60:
        return {"hmm_bull_prob": 0.33, "hmm_bear_prob": 0.33, "hmm_neutral_prob": 0.34}

    try:
        close = df["close"].to_numpy()
        returns = np.diff(np.log(close))
        volatility = np.abs(returns)
        
        X = np.column_stack([returns, volatility])
        
        # Fit Gaussian HMM
        model = GaussianHMM(n_components=n_states, covariance_type="diag", n_iter=100, random_state=42)
        model.fit(X)
        
        # Determine component order by mean returns (State with highest mean return = Bull)
        means = model.means_[:, 0]
        sorted_indices = np.argsort(means)
        bear_idx, neutral_idx, bull_idx = sorted_indices[0], sorted_indices[1], sorted_indices[2]
        
        # Current state probabilities
        curr_probs = model.predict_proba(X[-1:])[0]
        
        # 5-session forward transition probabilities: P(State_{t+5} | State_t)
        trans_mat = model.transmat_
        forward_probs = np.linalg.matrix_power(trans_mat, 5) @ curr_probs
        
        bull_p = float(forward_probs[bull_idx])
        bear_p = float(forward_probs[bear_idx])
        neutral_p = float(forward_probs[neutral_idx])
        
        # Normalize sum to 1.0
        total = bull_p + bear_p + neutral_p
        if total > 0:
            bull_p /= total
            bear_p /= total
            neutral_p /= total

        return {
            "hmm_bull_prob": round(bull_p, 3),
            "hmm_bear_prob": round(bear_p, 3),
            "hmm_neutral_prob": round(neutral_p, 3),
        }
    except Exception as e:
        logger.warning("hmm_calculation_failed", error=str(e))
        return {"hmm_bull_prob": 0.33, "hmm_bear_prob": 0.33, "hmm_neutral_prob": 0.34}
