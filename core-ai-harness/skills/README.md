# Skills - 能力层

AI 可调用的技能，编排多个 gates 的复杂操作。

## 技能列表

| 技能 | 作用 | 状态 |
|------|------|------|
| `gate-scanner/` | 门禁扫描 | 待实现 |
| `gate-fixer/` | 门禁修复 | 待实现 |
| `code-review/` | 代码审查 | 待实现 |
| `project-onboard/` | 项目安装 | 待实现 |
| `gate-report/` | 质量报告 | 待实现 |

## 调用方式

AI 可以主动调用，或通过 commands 触发。

```
/gates check <files>    # 调用 gate-scanner
/gates fix <files>      # 调用 gate-fixer
```
