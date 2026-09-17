# AFS Sentinel

Early-warning system that autonomously screens IDX-listed non-financial companies for earnings-manipulation and distress signals, and surfaces them to a single analyst for triage.

## Language

### Subjects & data

**Emiten**:
A company listed on IDX, identified by its ticker symbol.
_Avoid_: Ticker (as a noun for the company), stock, issuer

**Universe**:
The set of Emiten the system screens on each Audit Run; financial-sector Emiten are always excluded.
_Avoid_: Watchlist, portfolio

**Report Period**:
The fiscal quarter a financial report covers (e.g. 2025-Q3), identified by its report date — distinct from when the system detected anything.
_Avoid_: Quarter (ambiguous with detection time), periode deteksi

**Insider Filing**:
An IDX disclosure of a share transaction by an insider or major (≥5%) shareholder of an Emiten; an event with a transaction date, not tied to a Report Period. It does not by itself identify directors or commissioners.
_Avoid_: Insider trade, ordal transaction

### Screening

**Forensic Rule**:
One named, deterministic indicator (e.g. Sloan Accrual Ratio) evaluated against an Emiten's data.
_Avoid_: Plugin, check, module, indikator

**Rule Finding**:
The outcome of one Forensic Rule for one Emiten and Report Period: `PASS`, `WARNING`, `RED_FLAG`, or `INSUFFICIENT_DATA` (the rule could not be evaluated and is left out of the Composite Risk Score — never treated as a pass), with the computed value and threshold.
_Avoid_: Alert, flag status, SEVERE, ALERT, FLAGGED, N/A

**Composite Risk Score**:
A 0–100 weighted aggregate of the Rule Findings for one Emiten and Report Period, computed for every Emiten in the Universe whether or not an Incident exists. It is **Low Confidence** when the rules that could be evaluated carry less than half of the total weight.
_Avoid_: Risk score, forensic score

**Audit Run**:
One autonomous execution of the screening pipeline over the Universe, recorded whether or not it finds anything.
_Avoid_: Job, scan, cron run

**Backtest**:
A replay of the Forensic Rules over an Emiten's historical Report Periods to show when it would first have been flagged relative to a known real-world failure; it creates no Incidents and sends no notifications.
_Avoid_: Simulation, historical run

### Incidents & triage

**Incident**:
The record of risk findings for one Emiten in one Report Period that needs triage — it exists only once the Incident Severity reaches `MODERATE`. Insider Filings attach to the Emiten's latest Report Period Incident, and can re-score it within the same Report Period.
_Avoid_: Alert, ticket, case

**Incident Severity**:
The grade derived from the Composite Risk Score: `LOW`, `MODERATE`, or `CRITICAL`. A `RED_FLAG` on a core rule (Sloan, earnings–cash divergence, Altman) raises it to at least `MODERATE`; a Low Confidence score can never be `CRITICAL`.
_Avoid_: Risk level, RED FLAG (that is a Rule Finding)

**Escalation**:
An increase in an existing Incident's Incident Severity on a later Audit Run; it updates the same Incident rather than creating a new one.
_Avoid_: Re-alert, new incident

**Triage Status**:
The analyst's disposition of an Incident: `UNTRIAGED`, `INVESTIGATING`, `RESOLVED` (acted upon), or `DISMISSED` (false alarm; suppresses re-notification unless Escalated).
_Avoid_: Ticket status

**Analyst**:
The single person who receives notifications and triages Incidents.
_Avoid_: User, assignee
