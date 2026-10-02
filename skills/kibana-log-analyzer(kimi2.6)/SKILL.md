---
name: kibana-log-analyzer
description: >
  This skill should be used when the user needs to analyze Kibana/Elasticsearch error logs
  from Java microservices, perform root cause analysis (RCA), trace distributed call chains
  via correlation_id, or generate error analysis reports. Triggers include:
  "分析Kibana日志", "查看错误日志", "排查线上问题", "error log analysis",
  "Kibana日志排查", "根因分析", "trace日志", "correlation_id追踪",
  "微服务错误排查", "Java异常分析", "日志聚合分析", "线上故障排查",
  "分析action索引", "分析trace索引", "错误日志汇总", "日志报告".
---

# Kibana Log Analyzer

## Overview

Analyze Kibana/Elasticsearch error logs from Java microservices. Group ERROR-level logs by `app`, `action`, and `error_code`, fetch detailed trace content, reconstruct distributed call chains via `correlation_id`, and perform deep root cause analysis with source code correlation. The skill dispatches parallel SubAgents for per-group detailed analysis and synthesizes a comprehensive summary report.

## When to Use

- User asks to analyze Kibana error logs or trace logs.
- User needs root cause analysis for production incidents.
- User wants to understand error patterns, frequency, or impact.
- User needs distributed call chain reconstruction via `correlation_id`.
- User requests error log summary reports or detailed per-group reports.

## Prerequisites

- `KIBANA_URL` environment variable or user-provided Kibana URL.
- `KIBANA_AUTH` environment variable (optional) in `user:password` format for basic auth.
- Python 3 available in the environment.
- Access to source code repository for deep RCA (optional but strongly recommended).

## Core Workflow

### Phase 1: Gather Input Parameters

Determine the following from user input or defaults:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `kibana_url` | `$KIBANA_URL` | Kibana base URL |
| `index_date` | Current date `yyyy.mm.dd` | Index suffix or `*` for wildcard |
| `app_filter` | None (all apps) | Comma-separated app names to filter |
| `time_range` | `now-1h` | Elasticsearch range query for `@timestamp` |
| `result_level` | `ERROR` | Log result level to analyze |

Ask the user for any missing required parameters. Do NOT proceed without `kibana_url` and `index_date`.

### Phase 2: Execute Grouping Query

Run the grouping query script to aggregate ERROR logs:

```bash
python scripts/query_error_groups.py <kibana_url> <index_date> [app_filter] [time_range]
```

The script returns a JSON response with aggregations structured as:

```
by_app → by_action → by_error → sample_hit
```

Each leaf node contains:
- `key`: the error_code value
- `doc_count`: number of occurrences
- `sample_hit.hits.hits[0]._source`: one representative log record

Parse the aggregations to build a list of error groups. Each group is uniquely identified by `(app, action, error_code)`.

### Phase 3: Fetch Trace Details for Each Group

For each group's sample hit:

1. Extract the `id` field from the sample action log.
2. Query the corresponding trace-* index for detailed content:

```bash
python scripts/query_trace_detail.py <kibana_url> <index_date> <trace_id>
```

3. The script first tries `_doc/{trace_id}`, then falls back to `_search` by `id` field if 404.
4. Extract the `content` field from the trace response — this contains the full stack trace or detailed error message.

### Phase 4: Reconstruct Correlation Chain (Optional but Recommended)

If the sample log contains `correlation_id`:

1. Query all action-* records sharing the same `correlation_id`:

```bash
python scripts/query_trace_chain.py <kibana_url> <index_date> <correlation_id>
```

2. Sort results by `@timestamp` ascending to reconstruct the call timeline.
3. Follow `ref_id` → parent `id` relationships to identify the originating failure.
4. Note the first ERROR or WARN in the chain — this is often the root cause service.

### Phase 5: Source Code Correlation (Optional but Strongly Recommended)

If source code is accessible:

1. Search the codebase for the `app` module name to locate the service.
2. Search for the `action` name to find the relevant controller / service method.
3. Search for the `error_code` or exception class mentioned in `error_message` / `content`.
4. Extract relevant code snippets (method bodies, exception handlers, config files) to include in SubAgent analysis.

Reference `references/java_troubleshooting.md` for common Java exception patterns and source-level debugging heuristics.

### Phase 6: Dispatch SubAgents for Detailed Analysis

**CRITICAL: One SubAgent per error group. Parallel dispatch for all groups.**

For each error group `(app, action, error_code)`:

1. Prepare the SubAgent input package:
   - Group metadata (app, action, error_code, doc_count, time_range)
   - Sample action log (JSON)
   - Sample trace log / `content` (JSON or raw text)
   - Correlation chain logs (JSON array, if available)
   - Relevant source code snippets (if available)

2. Dispatch a SubAgent using the prompt template from `references/subagent_prompt_template.md`.

3. The SubAgent must produce a standalone markdown report with:
   - Executive Summary
   - Error Pattern Analysis
   - Root Cause Analysis
   - Impact Assessment
   - Fix Recommendations
   - Additional Context Needed

4. Collect all SubAgent reports.

### Phase 7: Synthesize Summary Report

After all SubAgents complete, produce a master summary report containing:

1. **Overview**: Total error groups analyzed, total error count, time range.
2. **Error Group Summary Table**:
   | App | Action | Error Code | Count | Severity | Status |
3. **Top Issues**: Ranked by impact (frequency × severity).
4. **Cross-Cutting Patterns**: Common root causes spanning multiple groups.
5. **Recommended Actions**: Prioritized fix list with owner assignment suggestions.
6. **Appendix**: Links to each SubAgent's detailed report.

## Query Reference

For DSL syntax details, curl templates, and query variations, see `references/dsl_templates.md`.

For index field definitions and relationships, see `references/index_schema.md`.

## Constraints & Rules

- **DEFAULT**: Analyze `result: ERROR` logs from the last 1 hour (`now-1h`).
- **GROUPING**: Always group by `app` → `action` → `error_code` before analysis.
- **ONE SAMPLE PER GROUP**: Do NOT analyze every single log entry individually.
- **SUBAGENTS REQUIRED**: Every group MUST be analyzed by a dedicated SubAgent. Never skip SubAgent dispatch.
- **ROOT CAUSE REQUIRED**: Surface-level conclusions are unacceptable. Every report must explain WHY the error occurs.
- **NO CODE MODIFICATION**: This skill is for analysis and reporting only. Do NOT modify any source code.
- **TRACE FALLBACK**: If `_doc` API returns 404, always fall back to `_search` by `id` field.
- **CORRELATION TRACING**: When `correlation_id` is present, always attempt call chain reconstruction.

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/query_error_groups.py` | Aggregate ERROR logs by app/action/error_code |
| `scripts/query_trace_detail.py` | Fetch detailed trace content by log id |
| `scripts/query_trace_chain.py` | Reconstruct distributed call chain by correlation_id |

## References

| File | Purpose |
|------|---------|
| `references/index_schema.md` | Index naming, field definitions, relationships |
| `references/dsl_templates.md` | Elasticsearch DSL query templates and curl examples |
| `references/java_troubleshooting.md` | Common Java exception patterns and RCA heuristics |
| `references/subagent_prompt_template.md` | SubAgent dispatch prompt template |
