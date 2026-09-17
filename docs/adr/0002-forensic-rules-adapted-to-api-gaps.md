# Forensic Rules adapted to what the Sectors API actually returns

Verification of Sectors API v2 showed no accounts receivable, no retained earnings in quarterly data, `ebit` sometimes null, and quarterly history only from 2020-Q1. We therefore drop Beneish DSRI entirely (not shown anywhere, including Telegram and the UI), drop Beneish TATA because it is the same formula as the Sloan Accrual Ratio and would double-count accruals, compute Sloan over average total assets, and run Altman as an explicitly labelled "Adapted Z''" (X₂ proxied by total_equity/total_assets, X₃ falling back to operating_pnl, X₄ at book value) with a stricter distress threshold to offset the upward bias of the X₂ proxy.

## Consequences

- The incident page must disclose the Altman adaptation and its limitation.
- Any claim of early detection before 2020 (e.g. "WSKT 22 months earlier") cannot be backed by API data.
