---
name: architecture
description: "Layered architecture constraints - Controller → Service → Repository"
category: architecture
---

# Architecture Rules

## Layer Dependencies

### ✅ Allowed Direction
```
Controller → Service → Repository
```

### ❌ Forbidden Dependencies
- Controller directly accessing Repository
- Service accessing Controller
- Repository accessing Service or Controller

## Package Structure

### Standard Layout
```
src/main/java/com/example/
├── controller/     # HTTP endpoints
├── service/        # Business logic
├── repository/     # Data access
├── domain/         # Entities and value objects
└── config/         # Configuration
```

### Naming Conventions
- Controllers: `*Controller`
- Services: `*Service` (interface) + `*ServiceImpl`
- Repositories: `*Repository`
- Entities: Domain model classes

## Dependency Injection

### ✅ Good
```java
@Service
public class UserService {
    private final UserRepository userRepository;
    
    public UserService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }
}
```

### ❌ Bad
```java
@Controller
public class UserController {
    @Autowired
    private UserRepository userRepository;  // Direct DB access!
}
```

## Transaction Boundaries

- Transactions should start at Service layer
- Repository methods should not have `@Transactional`
- Controller should not manage transactions

## Module Boundaries

### FBR-Specific Rules (when FBR profile enabled)
- `*WebServiceImpl` cannot import from `repository` package
- `*-service-interface` cannot have `@Inject` annotations
- Controllers must be in `controller` package
- Kafka handlers must be in `kafka` package
