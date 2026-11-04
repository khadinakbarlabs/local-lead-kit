# Report and handoff

Give the answer in the form requested (CSV, ranked list, comparison, rewrite, or short brief). Use the available evidence, not the requested target count. For a finished toolbox run, `report <plan>` reads the cached evidence locally, including available fields, source links, row count, truncation, and the private result path. Inspect the actual rows or OUTPUT before stating a finding.

- **Answer:** lead with the outcome in the user's words. For incomplete results, state what was observed.
- **Evidence:** include the returned URL or exact run as appropriate, observation date, market and relevant samples. Identify unavailable values and simulation flags.
- **Coverage:** show how many items were requested, observed and reviewed if known. Explain missing pages, truncated reads and failed substeps.
- **Next step:** suggest one concrete action that answers an open question. Offer a saved brief when it helps the user resume.

For example, “Of the 25 businesses requested, the saved run returned 18. Ten sites had visible email contacts. The CSV includes the source site for each address.” Only use figures verified for that run.

## Resume on the same device

Use the same private toolbox workspace across Claude Code, Codex, Cursor or another local host. All of these actions work offline:

- `save-brief --task <task-id> --goal "<goal>" --deliverable "<format>" --next-step "<follow-up>" [--plan <digest>]` saves a new brief and optionally binds the approved plan from that Actor. Store the minimum needed to continue; never include credentials.
- `history` lists briefs; `reopen <brief-id>` shows the task, original scope, next step and whether a saved result exists.
- `compare <first-plan> <second-plan>` compares distinct cached runs for the same Actor and input. It reports scope, completeness and exact row-value differences. For a business conclusion, compare the relevant fields by entity, language, currency and date, and label different build versions.

For a cross-agent handoff, provide the brief ID, requested deliverable, evidence location and outstanding question. Do not start a new run to reopen a brief. If a fresh observation is requested, prepare a separately approved, date-labelled plan.
