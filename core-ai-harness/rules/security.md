---
name: security
description: "Security coding guidelines - no hardcoded secrets, no SQL injection, proper exception handling"
category: security
---

# Security Rules

## Hardcoded Secrets

### ❌ Forbidden
```java
// BAD
String apiKey = "sk-1234567890abcdef";
String password = "admin123";
String secretKey = Base64.getDecoder().decode("c2VjcmV0");
```

### ✅ Required
```java
// GOOD - use environment variables or config
String apiKey = System.getenv("API_KEY");
String password = configService.getSecret("db.password");
```

## SQL Injection

### ❌ Forbidden - String Concatenation
```java
// BAD
String query = "SELECT * FROM users WHERE id = '" + userId + "'";
```

### ✅ Required - Parameterized Queries
```java
// GOOD
PreparedStatement stmt = conn.prepareStatement("SELECT * FROM users WHERE id = ?");
stmt.setString(1, userId);
```

## Exception Handling

### ❌ Forbidden - Catch-All RuntimeException
```java
// BAD
try {
    riskyOperation();
} catch (Exception e) {
    throw new RuntimeException(e);  // Loses context
}
```

### ✅ Required - Specific Exceptions
```java
// GOOD
try {
    riskyOperation();
} catch (IOException e) {
    throw new BusinessException("Operation failed", e);
}
```

### ❌ Forbidden - Empty Catch Blocks
```java
// BAD
try {
    riskyOperation();
} catch (Exception e) {
    // ignored
}
```

## Logging Sensitive Data

### ❌ Forbidden
```java
// BAD
log.info("User login: password={}", password);
log.debug("API key: {}", apiKey);
```

### ✅ Required
```java
// GOOD
log.info("User login successful for userId={}", userId);
log.debug("API call completed");
```

## Input Validation

Always validate external input:
- Length limits
- Format validation (regex)
- Type checking
- Business rule validation
