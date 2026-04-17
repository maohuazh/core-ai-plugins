
# AI时代个人知识库与智能博客系统 PRD（完整设计稿）

## 一、问题背景与本质思考

在大模型时代，传统博客与个人知识库正在发生结构性变化：

过去：
- 内容发布工具
- SEO驱动信息分发
- 被动式知识存储

现在：
- 用户通过AI直接获取答案
- 知识从展示转向可计算与可推理
- 系统从“页面”转向“认知结构”

结论：
个人知识库 = 人类表达 + AI推理结构 + 可演进认知系统

---

## 二、核心设计目标

必须同时满足三方：

1. 人类作者：写作无负担、流畅表达
2. 人类读者：清晰阅读、多层理解
3. AI系统：结构化理解与推理

---

## 三、设计原则

- Human Flow First（写作心流优先）
- Structure Hidden, Not Absent（结构隐藏但存在）
- AI as Consumer（AI消费结构但不控制写作）
- Progressive Enhancement（能力渐进增强）
- Article is Source of Truth（文章为唯一真相源）

---

## 四、系统总体架构

三层结构：

1. Human Experience Layer
- 写作
- 阅读
- 发布

2. Knowledge Structuring Layer
- Atom
- Embedding
- Graph
- Versioning

3. AI Intelligence Layer
- RAG
- Agent
- Reasoning

---

## 五、核心数据模型

Article：
- id
- content
- title
- tags
- visibility
- version

Atom：
- atom_id
- article_id
- type
- content
- embedding
- semantic_id
- status

Relation：
- from_atom
- to_atom
- relation_type

---

## 六、分阶段产品需求

---

# Phase 1：Pure Writing Experience

目标：
极致写作体验，无干扰心流

功能：
- Markdown编辑器
- 自动保存
- 全屏写作
- 标签系统
- 搜索
- 版本历史

UX：
- 无弹窗
- 无AI
- 无结构提示
- slash命令

架构：
- MongoDB存储
- Elasticsearch搜索
- 前端本地缓存

---

# Phase 2：Invisible Structuring

目标：
系统理解内容但用户无感知

功能：
- 自动Atom生成
- embedding生成
- 智能引用推荐

UX：
- 不展示结构
- hover轻提示
- 不打断写作

架构：
- Kafka pipeline
- NLP解析服务
- Atom存储
- 向量索引

---

# Phase 3：AI Reading Experience

目标：
提升阅读效率但不破坏体验

功能：
- AI摘要
- Ask This Article
- 段落解释

UX：
- AI默认折叠
- 内容优先
- 强引用

架构：
- RAG单文档检索
- Atom级上下文构建

---

# Phase 4：Knowledge OS

目标：
个人第二大脑

功能：
- 全局问答
- 跨文章聚合
- 推荐系统

UX：
- 记忆触发提示
- 多文档组合回答

架构：
- 向量数据库
- 多文档RAG
- 权限过滤

---

# Phase 5：AI Writing Assistant

目标：
AI辅助但不控制写作

功能：
- 补全
- 改写
- 引用提示

UX：
- 必须确认AI内容
- 不自动写入

架构：
- Prompt + RAG
- Agent系统

---

# Phase 6：Public AI Blog

目标：
可对话博客系统

功能：
- Ask Author
- 多视角阅读
- AI导航

UX：
- 对话式访问
- 问题驱动浏览

架构：
- Public RAG
- SEO + AI索引

---

## 七、核心机制

Atom生命周期：
Article -> Atom -> Embedding -> Graph

更新策略：
- Article为唯一真相源
- Atom为派生结构
- 通过版本控制保证一致性

---

## 八、核心结论

系统本质：

人类写作入口 + AI推理能力 + 知识结构化 = 认知操作系统

---

## 九、一句话总结

让人类像写博客一样表达，让AI像理解数据库一样理解知识。
