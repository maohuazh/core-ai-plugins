---
name: fp-paradigm
description: "Functional programming paradigm - immutable data, pure functions, Stream API"
category: fp
---

# FP Paradigm Rules

## Core Principles

1. **Immutable Data** - Never mutate state; use new instances
2. **Pure Functions** - Same input → same output, no side effects
3. **Stream API** - Process collections declaratively
4. **Optional over null** - Avoid null references

## Forbidden Patterns

### ❌ Traditional for loops
```java
// BAD
for (int i = 0; i < list.size(); i++) { ... }
```

### ❌ While/do-while loops
```java
// BAD
while (condition) { ... }
```

### ❌ Increment/decrement operators
```java
// BAD
i++; i--; ++i; --i;
```

### ❌ Parameter mutation
```java
// BAD
void process(List<String> items) {
    items.add("new");  // mutating parameter
}
```

### ❌ Returning null
```java
// BAD
public User findUser(String id) {
    if (notFound) return null;
}
```

### ❌ Mutable accumulators
```java
// BAD
List<String> result = new ArrayList<>();
for (Item item : items) {
    result.add(item.getName());
}
```

## Recommended Patterns

### ✅ Use Stream API
```java
// GOOD
list.stream()
    .map(Item::getName)
    .collect(Collectors.toList());
```

### ✅ Use Optional
```java
// GOOD
public Optional<User> findUser(String id) {
    return repository.findById(id);
}
```

### ✅ Use collect()
```java
// GOOD
List<String> names = items.stream()
    .map(Item::getName)
    .collect(Collectors.toList());
```

## Pragmatic Exceptions

These are acceptable when necessary:

- **Enhanced for-loops** at effect boundaries (I/O, logging)
- **Primitive array access** in performance-critical code
- **Simple adapters** that delegate to imperative code

## AST-Grep Rules

Each forbidden pattern has a corresponding AST-Grep rule:
- `no-traditional-for-loop`
- `no-while-loop`
- `no-do-while-loop`
- `no-increment-decrement`
- `no-parameter-mutation`
- `no-null-return`
- `no-mutable-accumulator`
