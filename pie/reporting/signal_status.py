"""Format signal status for market reports."""


from pie.core.signal_state import SignalState


def format_signal_status(
    state: SignalState,
    status: str,
    previous_strategy: str | None = None,
    current_strategy: str | None = None,
) -> list[str]:
    """
    Format SIGNAL STATUS section for the report.

    Args:
        state: Current signal state
        status: One of "NEW", "CHANGED", "EXISTING"
        previous_strategy: Previous strategy (only used if status="CHANGED")
        current_strategy: Current strategy (only used if status="CHANGED")

    Returns:
        List of formatted lines for the report
    """
    lines = [
        "SIGNAL STATUS",
        "=" * 13,
        "",
    ]

    # Trade status with emoji
    status_emoji = {"NEW": "🟢", "CHANGED": "🔄", "EXISTING": "⭐"}
    emoji = status_emoji.get(status, "")
    lines.append(f"Trade Status : {emoji} {status}")

    # Duration and trend started
    lines.append(
        f"Signal Age   : {state.signal_age_sessions} trading session(s)"
    )
    lines.append(
        f"Trend Since  : {state.trend_started_at:%d %b %Y, %H:%M %Z}"
    )

    # Show reason for status
    if status == "NEW":
        lines.extend(
            [
                "",
                f"Previous     : None",
                f"Current      : {state.last_regime.replace('_', ' ').title()}",
                "",
                "Reason",
                "------",
                "• Initial signal detected",
                "• Ready for potential entry",
            ]
        )
    elif status == "CHANGED":
        lines.extend(
            [
                "",
                f"Previous     : {previous_strategy}",
                f"Current      : {current_strategy}",
                "",
                "Reason",
                "------",
                "• Market regime or strategy has changed",
                "• Previous trade may need reassessment",
                "• Consider closing or adjusting existing position",
            ]
        )
    else:  # EXISTING
        lines.extend(
            [
                "",
                "No change since the previous report.",
                f"Regime       : {state.last_regime.replace('_', ' ').title()}",
                f"Strategy     : {state.last_strategy.replace('_', ' ').title()}",
            ]
        )

    return lines
