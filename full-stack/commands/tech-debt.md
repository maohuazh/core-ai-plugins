---
name: tech-debt
description: 技术债务盘点，识别待重构区域与过时依赖
triggers:
  - /tech-debt
parameters:
  - name: --scope
    description: 盘点范围 (code|deps|all)
    default: all
  - name: --output
    description: 输出文件路径
    default: tech-debt-report.md
---

# Tech Debt 技术债务盘点

系统性识别技术债务，为重构规划提供依据。

## 盘点维度

**代码异味**
- 重复代码
- 过长函数
- 过深嵌套
- 魔法数字

**过时依赖**
- 废弃包
- 版本落后
- 许可证风险

**待重构区域**
- 高复杂度模块
- 低测试覆盖区域
- 频繁变更文件

## 使用示例

```
/tech-debt
/tech-debt --scope=code
```