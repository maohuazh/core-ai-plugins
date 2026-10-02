## SubAgent Instructions for Kibana Log Analysis

Use this template when dispatching SubAgents for per-group deep analysis. Pass the following context to each SubAgent:

### Context to Pass
1. **Error Group Info**: app name, action name, error_code, total count, sample log id
2. **Sample Log Data**: full sample log record from action-* index
3. **Trace Detail**: content field from trace-* index (same id)
4. **Call Chain**: all related action-* logs via correlation_id
5. **Source Code Location**: the service path for this app (if known)

### SubAgent Task
```
Perform deep root cause analysis for this error group.

**Error Group**: app={APP}, action={ACTION}, error_code={CODE}
**Total Occurrences**: {COUNT}

**Sample Log**:
{SAMPLE_LOG_JSON}

**Trace Detail**:
{TRACE_CONTENT}

**Call Chain Context**:
{RELATED_LOGS}

Your tasks:
1. LOCATE the source code responsible for this error using app name, action name, and stack trace
2. TRACE the execution path from entry point to the error condition
3. IDENTIFY the root cause — the underlying code logic flaw, not just the error message
4. ASSESS impact scope: how many users/orders/services/transactions are affected
5. RATE severity: P0 (critical outage) to P4 (cosmetic/minor)
6. PROPOSE a fix: specific code changes with file paths and line references

Be thorough. Read the actual source code, not just the log messages.
Trace through the call chain to find the original trigger.
If the error is a symptom of a deeper issue (e.g., timeout causing cascade), identify that.
```

### SubAgent Output Format
```markdown
### Root Cause Analysis: {app}/{action}/{error_code}

#### Source Code Investigation
- Responsible files and methods
- Execution path to error (with file:line references)

#### Root Cause
{Clear explanation of the underlying cause, with code evidence}

#### Impact Assessment
- Scope: {users/services/data affected}
- Severity: P{0-4}
- Reasoning: {why this severity level}

#### Fix Proposal
{Specific code-level recommendation, including which files to modify and what to change}
```
