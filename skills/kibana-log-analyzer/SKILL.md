---
name: kibana-log-analyzer
description: >
  Analyze Kibana (Elasticsearch) error logs for root cause analysis. Use this skill whenever the user asks to analyze Kibana logs, check error logs, investigate microservice errors, trace correlation IDs, look up action/trace indices, find error causes, review log groups by app/action/error_code, do log-based RCA (Root Cause Analysis), or investigate distributed system failures via logs. Also trigger when the user mentions action-*, trace-* indices, correlation_id, ref_id chain tracing, Elasticsearch log queries, or wants to assess error impact and severity. If the user says "分析日志" (analyze logs), "查一下kibana" (check kibana), "帮我看看报错" (help me check errors), or any Chinese equivalents related to log investigation, use this skill. The skill queries action-* and trace-* indices, groups errors by (app, action, error_code), dispatches SubAgents for deep per-group analysis with source code context, and generates a comprehensive root cause report.
---

## Skill Overview

You are a senior DevOps + backend architect performing root cause analysis (RCA) on Kibana microservice logs. The analysis combines log data from Elasticsearch with source code investigation to identify root causes, assess impact, and propose fixes.

## Log Index Structure

### Indices
| Pattern | Purpose |
|---|---|
| `action-*` / `action-yyyy.mm.dd` | Base log records with trace chain metadata |
| `trace-*` / `trace-yyyy.mm.dd` | Detailed log records (stack traces, error details) |

For fixed-date queries, use format `action-yyyy.mm.dd` and `trace-yyyy.mm.dd` (e.g., `action-2026.04.17`).

### Key Fields

**action-* index**: `id`, `@timestamp`, `app`, `action`, `result` (OK/INFO/WARN/ERROR), `error_code`, `ref_id`, `correlation_id`, `error_message`, `context.{custom}`

**trace-* index**: `id`, `@timestamp`, `app`, `action`, `result`, `error_code`, `content`

**Relationship**: action-* and trace-* share the same `id`. Use `ref_id` (parent log ID) and `correlation_id` (full chain ID) on action-* to trace call chains. Use `content` on trace-* for stack traces and detailed error info.

## Analysis Workflow

Follow this exact sequence — do not skip steps or deviate.

### Step 1: Group Error Logs via Aggregation Query

Use the Kibana console proxy API to run an aggregation DSL query on the `action-*` index. This groups errors by `(app, action, error_code)` in a single query and returns one sample hit per group.

**cURL template:**

```bash
curl -s -X POST "${KIBANA_URL}/api/console/proxy?path=%2Faction-{date}%2F_search&method=GET" \
  -H 'Content-Type: application/json' \
  -d '<DSL_JSON>'
```

For rolling date pattern (last 1h), use `action-*` instead of a fixed date. For fixed-date queries, use `action-yyyy.mm.dd` format (e.g., `action-2026.04.17`).

**Aggregation DSL:**

```json
{
  "query": {
    "bool": {
      "must": [
        { "term": { "result": "ERROR" } },
        { "range": { "@timestamp": { "gte": "now-1h" } } }
      ]
    }
  },
  "size": 0,
  "aggs": {
    "by_app": {
      "terms": { "field": "app", "size": 50 },
      "aggs": {
        "by_action": {
          "terms": { "field": "action", "size": 50 },
          "aggs": {
            "by_error": {
              "terms": { "field": "error_code", "size": 50 },
              "aggs": {
                "sample_hit": {
                  "top_hits": {
                    "size": 1,
                    "sort": [{ "@timestamp": "desc" }],
                    "_source": ["id", "@timestamp", "app", "action", "error_code", "ref_id", "correlation_id", "error_message", "context"]
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

Parse the aggregation response to extract each group: `(app, action, error_code)`, count, and the sample hit record (which contains `id`, `correlation_id`, `error_message`, etc.).

If no results, expand the time window to 24h (`"gte": "now-24h"`) and inform the user.

### Step 2: Present Summary Table

For each group from the aggregation, present:

| Group (app + action + error_code) | Count | Sample Timestamp | error_message |
|---|---|---|---|
| ... | ... | ... | ... |

### Step 3: Fetch Trace Details

For each group's sample log `id`, query the `trace-*` index to get the detailed `content` field (stack traces, error details).

**Primary — use `_doc` API:**

```bash
curl -s -X GET "${KIBANA_URL}/api/console/proxy?path=%2Ftrace-{date}%2F_doc%2F{trace_id}&method=GET"
```

Use the same date format as the action index (e.g., `trace-2026.04.17`).

**Fallback — use `_search` if `_doc` returns 404:**
The id in action-* may differ from the trace index's document ID. In that case, search by the `id` field:

```bash
curl -s -X POST "${KIBANA_URL}/api/console/proxy?path=%2Ftrace-{date}%2F_search&method=GET" \
  -H "Content-Type: application/json" \
  -d '{"query": {"term": {"id": "{trace_id}"}}, "size": 10}'
```

Also trace the full call chain: use the sample's `correlation_id` to fetch all related `action-*` logs:

```bash
curl -s -X POST "${KIBANA_URL}/api/console/proxy?path=%2Faction-{date}%2F_search&method=GET" \
  -H "Content-Type: application/json" \
  -d '{"query": {"term": {"correlation_id": "{correlation_id}"}}, "size": 100}'
```

### Step 4: Dispatch SubAgents for Deep Analysis

**This step is mandatory — never skip.** Dispatch one SubAgent per error group. Each SubAgent receives:

- The error group summary (app, action, error_code, count, sample log data)
- The trace detail (`content` field from trace-* index)
- The call chain context (related action-* logs via correlation_id)
- Instructions to find and analyze the relevant source code

Each SubAgent must:
1. Locate the source code responsible for this error (use the `app` name, `action` name, and stack trace to find the relevant files)
2. Trace the execution path that leads to this specific error condition
3. Identify the **root cause** — not just the symptom, but the underlying code logic that triggers the error
4. Assess impact scope (how many users, orders, services are affected) and severity level (P0-P4)
5. Propose a fix or optimization with specific code-level recommendations

### Step 5: Compile Reports

After all SubAgents complete, produce two outputs:

1. **Summary Report** — one page covering all groups at a glance: total errors, group breakdown, top severity items, overall assessment

2. **Per-Group Detailed Reports** — one detailed report per error group including:
   - Error group identification
   - Sample log + trace detail
   - Call chain analysis
   - Source code analysis (with file paths and line references)
   - Root cause identification
   - Impact assessment (scope + severity)
   - Fix proposal or optimization suggestion

## Source Code Analysis Rules

When analyzing source code:
- Use `app` name to locate the service/module in the codebase
- Use `action` name to narrow down to the specific handler/method
- Use stack trace `content` to find the exact exception throw point
- Trace backward from the error point through the call chain to find the original trigger
- Check error handling paths — is the error caught/suppressed, or does it propagate?
- Look for common patterns: null checks, timeout configs, connection pool limits, missing configs, data inconsistencies

## Output Format

Use this structure for the final report:

```
# Kibana Log Analysis Report

## Executive Summary
- Analysis time window
- Total ERROR logs found
- Number of distinct error groups
- Overall severity assessment

## Error Group Overview
| # | app | action | error_code | Count | Severity | Root Cause Summary |
|---|-----|--------|------------|-------|----------|-------------------|

## Detailed Analysis (per group)

### Group N: {app} / {action} / {error_code}
- **Count**: N errors
- **Time Range**: first ~ last
- **Sample Log**: id, timestamp, error_message
- **Trace Detail**: stack trace summary from trace-* index
- **Call Chain**: correlation_id path analysis
- **Source Code Analysis**:
  - Responsible file(s): path:line
  - Execution path to error
  - Root cause
- **Impact Assessment**:
  - Scope: what's affected
  - Severity: P0-P4
- **Fix Proposal**: specific code-level recommendation
```

## Hard Constraints

- Do NOT analyze logs one by one — always group first, then analyze via SubAgents
- Do NOT modify any code — this is read-only analysis
- Do NOT skip SubAgent dispatch — every error group must have a SubAgent analysis
- Do NOT give surface-level conclusions — every finding must include root cause with source code evidence
- Do NOT change the default 1-hour window unless there are zero results (then expand to 24h)
