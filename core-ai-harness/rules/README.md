# Rules - AI 认知层

自然语言规则文档，AI Agent 在生成代码时自动阅读并遵守。

## 规则文件

- `fp-paradigm.md` - 函数式编程范式
- `architecture.md` - 分层架构约束
- `security.md` - 安全编码策略
- `code-style.md` - 通用代码风格

## 设计理念

Rules 只写**意图和原则**，不写精确匹配模式。
精确匹配交给 Gates 的 AST 规则。

## 与 Gates 的区别

```
Rules 说：  "避免使用传统 for 循环，优先使用 Stream API 处理集合操作"
             ↑ 自然语言，AI 理解意图

Gates 说：  pattern: for ($INIT; $COND; $UPDATE) { $BODY }
             ↑ AST pattern，机器精确匹配
```

Rules 是"道德准则"，Gates 是"法律条文"。
