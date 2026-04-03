---
name: db-migrate
description: 数据库迁移脚本生成与版本追踪
triggers:
  - /db-migrate <变更描述>
parameters:
  - name: 变更描述
    required: true
    description: Schema变更说明
  - name: --type
    description: 迁移类型 (create|alter|drop)
---

# DB Migrate 数据库迁移

生成数据库迁移脚本，支持版本追踪与回滚。

## 执行流程

```
分析Schema → 生成迁移脚本 → 生成回滚脚本 → 输出文件
```

## 使用示例

```
/db-migrate 添加用户登录日志表
/db-migrate 修改订单表添加状态字段 --type=alter
```