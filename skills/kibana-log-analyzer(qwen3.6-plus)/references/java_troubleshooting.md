# Java Microservice Troubleshooting Guide

## Common Exception Patterns & Root Cause Mapping

### NullPointerException (NPE)
- **Typical causes**: Missing dependency injection, uninitialized field, missing config value, null return from external service.
- **Source indicators**: Line number in stack trace points to dereference site.
- **Fix patterns**: Add `@NonNull` / `@Nullable` annotations, use `Optional`, add null-check guards, validate upstream responses.

### IllegalArgumentException / IllegalStateException
- **Typical causes**: Invalid parameter passed to method, object in wrong state for operation.
- **Source indicators**: Usually thrown explicitly in business logic or validation layer.
- **Fix patterns**: Strengthen input validation, add state-machine checks, improve error messages.

### DataAccessException / SQLException
- **Typical causes**: Connection pool exhaustion, deadlock, constraint violation, missing index causing timeout.
- **Source indicators**: Caused-by chain shows JDBC driver or ORM (MyBatis/Hibernate) frame.
- **Fix patterns**: Check connection pool metrics, review transaction boundaries, add retry with backoff, optimize queries.

### FeignException / WebClientResponseException / RestClientException
- **Typical causes**: Downstream service returned 4xx/5xx, timeout, circuit breaker open.
- **Source indicators**: HTTP status code and response body in exception message.
- **Fix patterns**: Add fallback / degrade logic, review timeout configs, check downstream health, add idempotency keys.

### TimeoutException / HystrixTimeoutException / Resilience4j
- **Typical causes**: Slow downstream, thread pool saturation, long GC pause.
- **Source indicators**: Timeout duration in message, preceding logs show long latency.
- **Fix patterns**: Increase timeout if legitimate slowness, optimize hot path, scale resources, async processing.

### ClassNotFoundException / NoClassDefFoundError
- **Typical causes**: Missing dependency in classpath, version conflict (fat jar shading), classloader isolation issue.
- **Source indicators**: Class name in exception message.
- **Fix patterns**: Check Maven/Gradle dependency tree, resolve version conflicts, verify packaging.

### OutOfMemoryError
- **Typical causes**: Memory leak, oversized batch processing, insufficient heap for traffic spike.
- **Source indicators**: GC logs preceding error, heap dump on OOM.
- **Fix patterns**: Analyze heap dump, reduce batch size, tune GC, scale horizontally.

## Correlation ID Tracing Strategy

1. Start from ERROR log in action-* index.
2. Extract `correlation_id`.
3. Query all action-* records with same `correlation_id`, sorted by `@timestamp` asc.
4. Build call chain: follow `ref_id` → parent `id` relationships.
5. Identify first ERROR or WARN in the chain — often the originating failure.
6. Query trace-* for the originating log's `id` to get full stack trace in `content`.

## Impact Assessment Heuristics

| Factor | High Impact | Medium Impact | Low Impact |
|--------|------------|---------------|------------|
| Frequency | >100/min | 10-100/min | <10/min |
| Affected users | All / core flow | Partial / edge case | Internal / background |
| Data integrity | Data loss / corruption | Stale data | None |
| SLA breach | >5min outage | Intermittent degradation | Single request failure |
| Downstream cascade | Multiple services affected | One downstream affected | Isolated |
