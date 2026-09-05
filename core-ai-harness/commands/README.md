# Commands - 用户入口

用户在 Claude Code 中直接使用的斜杠命令。

## 命令列表

| 命令 | 作用 | 状态 |
|------|------|------|
| `/gates` | 门禁总控 | 待实现 |
| `/gate-check` | 快速扫描 | 待实现 |
| `/gate-install` | 安装到项目 | 待实现 |

## 使用示例

```bash
# 检查变更文件
/gates check --changed

# 检查指定文件
/gate-check src/main/java/**/*.java

# 安装到当前项目
/gate-install
```
