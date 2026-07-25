# Project Rules

- Do not spend extra effort writing or running unit tests unless explicitly requested by the user.
- Never fill missing or null market data, prices, or indicator values with 0. Either forward-fill previous valid values, drop null rows, or mark as invalid/None.
- Always display the locally rendered dashboard/tables in the response for user review BEFORE committing and pushing code to Git.
