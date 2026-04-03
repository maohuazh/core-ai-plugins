---
name: explore
description: 代码库探索，理解现有架构与关键路径
triggers:
  - /explore <目标>
parameters:
  - name: 目标
    required: true
    description: 要探索的模块/功能
  - name: --depth
    description: 探索深度 (shallow|medium|deep)
    default: medium
---

# Explore 代码探索

深度分析代码库，输出架构理解与必读文件清单。

## 执行流程

```
定位入口 → 路径追踪 → 层次映射 → 文件筛选 → 输出报告
```

## 使用示例

```
/explore 用户认证模块
/explore 支付流程 --depth=deep
```