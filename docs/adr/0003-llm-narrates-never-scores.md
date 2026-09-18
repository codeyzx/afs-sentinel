# The LLM narrates an Incident, it never scores one

`docs/system-rules.md` §8 requires that every number and sentence on screen be traceable to API data
or to a rule in that document — which is why "Rekomendasi Aksi Sistem" was cut from the mockup. An
Incident Insight is LLM-generated prose, so it cannot meet that bar as written. We still want it:
the deterministic `headline` strings are accurate but read like a spreadsheet, and the single
Analyst has to decide in seconds which Incident to open first.

We resolve the conflict by making the LLM a translator rather than an analyst:

- It receives only facts this Audit Run already computed — ticker, Report Period, Composite Risk
  Score, Incident Severity, and per Rule Finding the status, value, thresholds, headline and the
  raw report figures. It never receives price, market cap, or anything from outside the run.
- Its output is a fixed JSON shape (what happened / why it matters / what to check) and can only be
  displayed. It never feeds back into the Composite Risk Score or the Incident Severity.
- It is labelled "Ringkasan AI" on the web and prefixed 🤖 in Telegram, and the block states that
  the official numbers are in the Rule Findings below it.
- Versions are kept in `incident_insights` with the model and prompt version, so what the Analyst
  read can be reconstructed later.

The alternative we rejected was full analysis with recommended actions. For an early-warning system
whose entire value is that a human can check its arithmetic, a confident machine recommendation that
turns out wrong costs more credibility than the feature is worth.

## Consequences

- §8 now carries an explicit, narrow exception for blocks labelled as AI-generated.
- Enforcement of "do not invent numbers" is by prompt only. We considered rejecting output
  containing numbers absent from the input, but legitimate narration rephrases figures ("13,8%" from
  `0.138`, "turun sepertiga", "tiga dari enam rule") and the validator would reject correct
  sentences. We accept the residual risk and rely on the label plus the evidence shown beneath.
- The Insight phase runs between the Emiten loop and the Telegram dispatch, on its own session. A
  Gemini outage costs a blank block and a line in the run log; the Audit Run still reports SUCCESS.
- A missing `GEMINI_API_KEY` disables the feature silently rather than breaking the pipeline.
