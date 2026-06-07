# Sky-Lynx Weekly Persona Ecosystem Analysis — 2026-06-07

## Run summary
- Repository: `sky-lynx`
- Install step executed: `pip install -e .`
- Main pipeline executed: `python -m sky_lynx.analyzer analyze --dry-run --no-pr`
- Why dry-run: `claude` CLI is not installed in this environment, so live model inference could not run.

## Pipeline ingestion observations
- Usage facets for this week were unavailable in this environment (`~/.claude/usage-data/facets` missing), so session-derived metrics were empty.
- Contract data ingestion worked after rebuilding `st-factory` SQLite from JSONL.
- Successfully loaded during run:
  - 100 outcome records (analysis window inside `load_outcome_records(limit=100)`)
  - 6,888 research signals from `st-factory` query layer
- Missing optional sources in this environment:
  - IdeaForge DB
  - Metroplex DB
  - ClaudeClaw DB/telemetry
  - model-audit runner

## Persona ecosystem metrics (st-factory snapshot)
Source: `st-factory/data/persona_metrics.db` (rebuilt from JSONL immediately before analysis run).

### Outcomes
- Total outcome records: **10,000**
- Outcome distribution:
  - `deferred`: **9,489** (94.9%)
  - `rejected`: **251** (2.5%)
  - `build_failed`: **220** (2.2%)
  - `published`: **40** (0.4%)
- Average `overall_score`: **60.15** (range: 40.0–76.2)

### Improvement recommendations
- Total recommendations: **258**
- Status distribution:
  - `pending`: **258**
  - `applied`: **0**
  - `rejected`: **0**
- Target system distribution:
  - `pipeline`: **169**
  - `claude_md`: **26**
  - `agent`: **20**
  - `schedule`: **18**
  - `skill`: **10**
  - `routing`: **6**
  - `preference`: **5**
  - `persona`: **4**
- Priority distribution:
  - `medium`: **110**
  - `high`: **104**
  - `low`: **44**

### Research signals
- Total research signals: **6,888**
- Relevance split:
  - `high`: **4,120** (59.8%)
  - `medium`: **2,768** (40.2%)
- Top signal sources:
  - `gemini_research`: 1,823
  - `perplexity`: 1,071
  - `rss_scanner`: 1,007
  - `tool_monitor`: 879
  - `reddit`: 653
- Top domains:
  - `developer-tools`: 1,243
  - `ai-agents`: 1,129
  - `mcp-servers`: 1,112
  - `agent-skills`: 832
- Persona-tagged coverage: **41 personas** represented (top tags include `knuth` and `developer-tools`)

## Recommended CLAUDE.md updates (proposed, not auto-applied)

### 1) Add a weekly preflight section (high priority)
**Evidence:** Weekly run had 0 session facets and multiple missing optional data stores.  
**Proposed CLAUDE.md insertion:** under `Quick Commands`.

```bash
# Weekly preflight checks
test -d ~/.claude/usage-data/facets && ls ~/.claude/usage-data/facets | wc -l
test -f ~/projects/st-records/data/persona_metrics.db || python - <<'PY'
from contracts.store import ContractStore
s = ContractStore(); s.rebuild_sqlite(); s.close()
print("rebuilt persona_metrics.db from JSONL")
PY
```

### 2) Add recommendation backlog guardrail (high priority)
**Evidence:** 258/258 recommendations are pending; none applied or rejected.  
**Proposed CLAUDE.md insertion:** under `Key Decisions`.

- **Backlog guardrail**: if pending recommendations exceed 200, prioritize a triage pass before generating new medium/low-priority recommendations.

### 3) Add contract-store-first fallback mode guidance (medium priority)
**Evidence:** Facet sessions were unavailable, but contract-store signals were abundant and still actionable.  
**Proposed CLAUDE.md insertion:** under `Project Purpose` or `Data Sources`.

- When weekly usage facets are missing, continue analysis in **contract-store-first mode** (outcomes + recommendations + research signals) and explicitly mark confidence as reduced for session-behavior claims.

### 4) Add signal triage budget guidance (medium priority)
**Evidence:** 6,888 signals with 4,120 high-relevance entries create review pressure.  
**Proposed CLAUDE.md insertion:** under `Data Sources` or a new `Analysis Heuristics` section.

- For weekly runs, prioritize top 3 domains by count and top 5 recent high-relevance signals per domain before broadening scope.

### 5) Add conversion KPI callout in weekly output checklist (medium priority)
**Evidence:** Published outcomes are 0.4% vs deferred 94.9%, indicating a major conversion bottleneck.  
**Proposed CLAUDE.md insertion:** under `Testing Strategy` or a new `Weekly Output Checklist` section.

- Always report terminal outcome conversion (`published / total`) and deferred ratio trend week-over-week.

## Follow-up actions
- Re-run full live analysis once `claude` CLI is available in the execution environment.
- Consider adding an analyzer `--contract-store-only` mode to avoid generating dry-run placeholder recommendations when model execution is unavailable.
