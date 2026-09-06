---
name: gate-fixer
description: "Automatically fix common gate violations (FP patterns, mutable accumulators)"
---

# Gate Fixer

Automatically fixes common gate violations detected by AST-Grep rules.

## Usage

```
/gate-fixer [file1.java] [file2.java] ...
```

If no files specified, fixes all changed Java files in the working directory.

## Supported Fixes

### 1. no-traditional-for-loop → Stream API

**Before:**
```java
for (int i = 0; i < items.size(); i++) {
    process(items.get(i));
}
```

**After:**
```java
items.forEach(this::process);
```

### 2. no-parameter-mutation → New variables

**Before:**
```java
public void process(String input) {
    input = input.toUpperCase();
    System.out.println(input);
}
```

**After:**
```java
public void process(String input) {
    final String processedInput = input.toUpperCase();
    System.out.println(processedInput);
}
```

### 3. no-mutable-accumulator → Stream operations

**Before:**
```java
List<String> result = new ArrayList<>();
for (Item item : items) {
    result.add(item.getName());
}
```

**After:**
```java
List<String> result = items.stream()
    .map(Item::getName)
    .collect(Collectors.toList());
```

## How it works

1. Runs gate-scanner to find violations
2. For each violation with a known fix pattern, applies the transformation
3. Re-runs gate-scanner to verify fixes
4. Reports what was fixed and what requires manual intervention

## Limitations

- Only fixes violations with clear, safe transformation patterns
- Complex refactorings may require manual intervention
- Some fixes may introduce new issues (e.g., Stream operations on very large collections)
- Always review the changes before committing

## Integration

This skill is invoked automatically by the PostToolUse hook when violations are detected.
