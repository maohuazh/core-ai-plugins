---
name: code-style
description: "Code style guidelines - naming conventions, method length, import order"
category: code-style
---

# Code Style Rules

## Naming Conventions

### Classes
- **PascalCase**: `UserService`, `OrderRepository`
- **Descriptive**: Use full words, avoid abbreviations
- **Nouns**: Class names should be nouns or noun phrases

### Methods
- **camelCase**: `getUserById`, `calculateTotal`
- **Verb-first**: `get`, `set`, `calculate`, `validate`, `process`
- **Descriptive**: Method name should clearly describe what it does

### Variables
- **camelCase**: `userName`, `orderCount`
- **Meaningful**: Avoid single-letter names except in loops (`i`, `j`)
- **No abbreviations**: Use `customer` not `cust`

### Constants
- **UPPER_SNAKE_CASE**: `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT`
- **Static final**: All constants should be `static final`

## Method Length

### Guideline
- **Ideal**: 10-20 lines
- **Maximum**: 50 lines
- **Refactor**: If method exceeds 50 lines, extract helper methods

### Signs to Refactor
- Multiple responsibilities
- Deep nesting (3+ levels)
- Long parameter lists (5+ params)

## Import Order

### Standard Order
1. Java standard library (`java.*`, `javax.*`)
2. Third-party libraries (`org.*`, `com.*`)
3. Project-specific imports

### Example
```java
import java.util.List;
import java.util.Optional;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.example.domain.User;
import com.example.repository.UserRepository;
```

## Comments

### When to Comment
- **Why**: Explain business logic decisions
- **Complex algorithms**: Non-obvious implementations
- **Workarounds**: Temporary fixes with TODO references

### When NOT to Comment
- **Obvious code**: `// Get user by ID` before `getUserById()`
- **TODO without context**: Always include ticket/issue reference

### Good Comment Example
```java
// Retry 3 times because external API has intermittent timeouts
// See: OPS-1234
for (int retry = 0; retry < 3; retry++) {
    // ...
}
```

## File Organization

### Class Structure
1. Static fields
2. Instance fields
3. Constructors
4. Public methods
5. Private methods
6. Nested classes/interfaces

### Keep Files Focused
- **One class per file** (except inner classes)
- **Single responsibility**: Class should have one clear purpose
