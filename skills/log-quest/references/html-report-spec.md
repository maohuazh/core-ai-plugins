# HTML 报告规范

## 概述

定义 HTML 报告的结构、样式要求和安全规范。报告必须可离线查看，支持审阅与复核，所有动态内容必须经过 HTML 转义。

## 报告结构

### 必需章节

报告必须包含以下 10 个章节：

#### 1. 调查摘要

**内容**：
- 调查 ID 和生成时间
- 故障症状（用户报告的问题）
- 影响范围（受影响的服务、用户、订单等）
- 调查时间范围
- 主要结论（一句话总结）

**示例**：
```html
<section id="summary">
  <h2>调查摘要</h2>
  <dl>
    <dt>调查 ID</dt>
    <dd>INV-2026-10-10-001</dd>
    <dt>生成时间</dt>
    <dd>2026-10-10T11:30:00Z</dd>
    <dt>故障症状</dt>
    <dd>广告报表接口返回 500 错误</dd>
    <dt>影响范围</dt>
    <dd>report-service 服务，影响所有使用广告报表功能的商户</dd>
    <dt>调查时间</dt>
    <dd>2026-10-10T11:17:18Z - 2026-10-10T11:17:19Z</dd>
    <dt>主要结论</dt>
    <dd>SQL 查询引用了不存在的列 'channel'，导致语法错误</dd>
  </dl>
</section>
```

#### 2. 根因结论

**内容**：
- 根因分类（data_error / logic_error / flow_error / network_error / resource_error / config_permission_error / unknown）
- 根因陈述
- 置信度（high / medium / low / unknown）
- 置信度依据
- 支持证据列表

**示例**：
```html
<section id="root-cause">
  <h2>根因结论</h2>
  <dl>
    <dt>根因分类</dt>
    <dd><span class="badge badge-error">data_error</span></dd>
    <dt>根因陈述</dt>
    <dd>SQL 查询引用了不存在的列 'channel'，导致语法错误</dd>
    <dt>置信度</dt>
    <dd><span class="badge badge-high">high</span></dd>
    <dt>置信度依据</dt>
    <dd>
      <ul>
        <li>日志明确显示 SQL 语法错误（sqlState=42S22, errorCode=1054）</li>
        <li>数据库查询确认 channel 列不存在</li>
        <li>异常堆栈指向 SQL 执行位置</li>
      </ul>
    </dd>
    <dt>支持证据</dt>
    <dd>
      <ul>
        <li><a href="#ev-log-001">ev-log-001</a>: 广告报表查询失败</li>
        <li><a href="#ev-trace-001">ev-trace-001</a>: SQL 查询详情</li>
        <li><a href="#ev-sql-001">ev-sql-001</a>: 数据库查询确认列不存在</li>
      </ul>
    </dd>
  </dl>
</section>
```

#### 3. 关键事件时间线

**内容**：
- 按时间排序的关键事件
- 每个事件包含：时间、服务、事件描述、日志 ID、事件类型
- 标记最早已知失败点

**示例**：
```html
<section id="timeline">
  <h2>关键事件时间线</h2>
  <table>
    <thead>
      <tr>
        <th>时间</th>
        <th>服务</th>
        <th>事件</th>
        <th>日志 ID</th>
        <th>类型</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>2026-10-10T11:17:18.704Z</td>
        <td>upstream-service</td>
        <td>发起广告报表查询请求</td>
        <td><a href="#log-A1258818EADBFBE7C5BC">A1258818EADBFBE7C5BC</a></td>
        <td><span class="badge badge-normal">normal</span></td>
      </tr>
      <tr class="failure">
        <td>2026-10-10T11:17:18.704Z</td>
        <td>report-service</td>
        <td>SQL 查询失败：Unknown column 'channel'</td>
        <td><a href="#log-A1258818F02B8859C9E8">A1258818F02B8859C9E8</a></td>
        <td><span class="badge badge-failure">failure</span></td>
      </tr>
    </tbody>
  </table>
</section>
```

#### 4. 故障因果链

**内容**：
- 从触发条件到故障表现的因果链
- 每个步骤包含：描述、证据 ID
- 区分触发条件、直接原因、连锁反应、最终表现

**示例**：
```html
<section id="causal-chain">
  <h2>故障因果链</h2>
  <ol>
    <li>
      <strong>触发条件</strong>：开发人员编写 SQL 查询时引用了 channel 列
      <ul>
        <li>证据：<a href="#ev-trace-001">ev-trace-001</a></li>
      </ul>
    </li>
    <li>
      <strong>直接原因</strong>：ads_campaign_customers 表中不存在 channel 列
      <ul>
        <li>证据：<a href="#ev-sql-001">ev-sql-001</a></li>
      </ul>
    </li>
    <li>
      <strong>异常抛出</strong>：MySQL 返回语法错误（sqlState=42S22, errorCode=1054）
      <ul>
        <li>证据：<a href="#ev-trace-001">ev-trace-001</a></li>
      </ul>
    </li>
    <li>
      <strong>应用异常</strong>：应用抛出 UncheckedSQLException
      <ul>
        <li>证据：<a href="#ev-log-001">ev-log-001</a></li>
      </ul>
    </li>
    <li>
      <strong>最终表现</strong>：HTTP 响应返回 500 错误
      <ul>
        <li>证据：<a href="#ev-log-001">ev-log-001</a></li>
      </ul>
    </li>
  </ol>
</section>
```

#### 5. 日志证据

**内容**：
- 关键日志的详细信息
- 包含：日志 ID、时间、服务、级别、错误码、错误消息、异常堆栈
- 对长异常堆栈采用折叠展示

**示例**：
```html
<section id="log-evidence">
  <h2>日志证据</h2>
  <article id="ev-log-001">
    <h3>ev-log-001: 广告报表查询失败</h3>
    <dl>
      <dt>日志 ID</dt>
      <dd>A1258818F02B8859C9E8</dd>
      <dt>时间</dt>
      <dd>2026-10-10T11:17:18.704896811Z</dd>
      <dt>服务</dt>
      <dd>report-service</dd>
      <dt>级别</dt>
      <dd>ERROR</dd>
      <dt>错误码</dt>
      <dd>core.framework.db.UncheckedSQLException</dd>
      <dt>错误消息</dt>
      <dd>Unknown column 'channel' in 'where clause', sqlState=42S22, errorCode=1054</dd>
      <dt>异常堆栈</dt>
      <dd>
        <details>
          <summary>展开堆栈</summary>
          <pre><code>core.framework.db.UncheckedSQLException: Unknown column 'channel' in 'where clause'
    at core.framework.internal.db.DatabaseOperation.selectOne(DatabaseOperation.java:93)
    at core.framework.internal.db.DatabaseImpl.selectOne(DatabaseImpl.java:246)
    at app.report.service.BOAdsCampaignReportService.getAdsCampaignSummary(BOAdsCampaignReportService.java:34)
    ...</code></pre>
        </details>
      </dd>
    </dl>
  </article>
</section>
```

#### 6. 数据库验证

**内容**：
- 执行的数据库查询列表
- 每个查询包含：查询 ID、数据源、查询目的、查询语句、执行状态、返回行数、结果解释
- 明确标记查询状态（completed / no_rows / denied / timeout / unavailable / truncated）

**示例**：
```html
<section id="database-checks">
  <h2>数据库验证</h2>
  <article id="ev-sql-001">
    <h3>ev-sql-001: 检查 channel 列是否存在</h3>
    <dl>
      <dt>查询 ID</dt>
      <dd>Q1</dd>
      <dt>数据源</dt>
      <dd>mysql-report-db-replica (replica)</dd>
      <dt>查询目的</dt>
      <dd>验证 ads_campaign_customers 表中是否存在 channel 列</dd>
      <dt>查询语句</dt>
      <dd><code>SHOW COLUMNS FROM ads_campaign_customers LIKE 'channel'</code></dd>
      <dt>执行状态</dt>
      <dd><span class="badge badge-warning">no_rows</span></dd>
      <dt>返回行数</dt>
      <dd>0</dd>
      <dt>执行耗时</dt>
      <dd>15ms</dd>
      <dt>结果解释</dt>
      <dd>channel 列在 ads_campaign_customers 表中不存在</dd>
    </dl>
  </article>
</section>
```

#### 7. 反证与替代解释

**内容**：
- 与当前假设冲突的证据
- 其他可能的替代解释
- 说明为什么当前假设比替代解释更合理

**示例**：
```html
<section id="counter-evidence">
  <h2>反证与替代解释</h2>
  <article>
    <h3>替代解释 1：数据库 migration 未执行</h3>
    <p>可能 channel 列应该在最新的数据库 migration 中添加，但 migration 未执行。</p>
    <dl>
      <dt>支持证据</dt>
      <dd>无直接证据</dd>
      <dt>反证</dt>
      <dd>代码中从未引用过 channel 列，直到最近的提交</dd>
      <dt>结论</dt>
      <dd>可能性较低，当前假设（代码错误引用不存在的列）更合理</dd>
    </dl>
  </article>
</section>
```

#### 8. 未解决问题

**内容**：
- 缺失的日志
- 未授权的数据源
- 无法验证的假设
- 建议的下一步调查

**示例**：
```html
<section id="unresolved">
  <h2>未解决问题</h2>
  <ul>
    <li>无法确认 channel 列是否应该在数据库中存在（需要检查数据库 schema 设计文档）</li>
    <li>无法确认是否有其他接口也引用了 channel 列（需要全局代码搜索）</li>
    <li>建议：检查最近的代码提交，确认是谁引入了 channel 列的引用</li>
  </ul>
</section>
```

#### 9. 调查覆盖范围与限制

**内容**：
- 查询的时间范围
- 查询的服务范围
- 日志检索状态（completed / partial / failed）
- 数据库查询状态
- 部分失败说明
- 截断说明
- 分片失败说明
- 其他限制

**示例**：
```html
<section id="limitations">
  <h2>调查覆盖范围与限制</h2>
  <dl>
    <dt>查询时间范围</dt>
    <dd>2026-10-10T11:17:18Z - 2026-10-10T11:17:19Z（±30 分钟）</dd>
    <dt>查询服务范围</dt>
    <dd>report-service, upstream-service</dd>
    <dt>日志检索状态</dt>
    <dd><span class="badge badge-success">completed</span></dd>
    <dt>数据库查询状态</dt>
    <dd><span class="badge badge-success">completed</span></dd>
    <dt>部分失败</dt>
    <dd>无</dd>
    <dt>截断</dt>
    <dd>无</dd>
    <dt>限制说明</dt>
    <dd>
      <ul>
        <li>日志索引延迟约 5 秒，可能遗漏最近 5 秒内的日志</li>
        <li>数据库查询使用从库，可能存在复制延迟</li>
      </ul>
    </dd>
  </dl>
</section>
```

#### 10. 证据索引

**内容**：
- 所有证据的索引列表
- 每条证据包含：证据 ID、类型、来源、摘要
- 便于快速查找和追溯

**示例**：
```html
<section id="evidence-index">
  <h2>证据索引</h2>
  <table>
    <thead>
      <tr>
        <th>证据 ID</th>
        <th>类型</th>
        <th>来源</th>
        <th>摘要</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><a href="#ev-log-001">ev-log-001</a></td>
        <td>log</td>
        <td>action-2026.10.10</td>
        <td>广告报表查询失败：Unknown column 'channel'</td>
      </tr>
      <tr>
        <td><a href="#ev-trace-001">ev-trace-001</a></td>
        <td>log</td>
        <td>trace-2026.10.10</td>
        <td>SQL 查询详情：SELECT COUNT(*) FROM ads_campaign_customers WHERE channel IN (...)</td>
      </tr>
      <tr>
        <td><a href="#ev-sql-001">ev-sql-001</a></td>
        <td>sql</td>
        <td>mysql-report-db-replica</td>
        <td>SHOW COLUMNS FROM ads_campaign_customers LIKE 'channel' 返回 0 行</td>
      </tr>
    </tbody>
  </table>
</section>
```

---

## 样式要求

### 1. 优先级展示

- 优先展示已验证结论
- 避免将整段原始日志堆叠成报告
- 使用折叠区展示长异常堆栈
- 限制总报告大小（建议不超过 5MB）

### 2. 时间展示

- 时间统一展示时区（建议使用 UTC）
- 保留原始时间戳以供核查
- 明确说明时区转换

### 3. 置信度展示

- 置信度应有解释，不应仅展示颜色或等级
- 使用徽章（badge）展示置信度等级
- 说明置信度评估依据

### 4. 数据库结果展示

- 明确标记数据源、查询状态和执行限制
- 使用徽章展示查询状态
- 说明查询状态的含义

### 5. 长内容处理

- 对长异常堆栈采用折叠展示
- 保留原始证据引用
- 限制单条日志的展示长度

---

## 安全规范

### 1. HTML 转义

**所有动态内容必须经过 HTML 转义**：
- 日志消息
- 异常堆栈
- SQL 查询语句
- 数据库查询结果
- 业务字段
- 用户输入

**转义规则**：
```
< → &lt;
> → &gt;
& → &amp;
" → &quot;
' → &#39;
```

**禁止行为**：
- ❌ 不得直接拼接 innerHTML
- ❌ 不得将日志内容当作 HTML 模板
- ❌ 不得执行日志中的 JavaScript

### 2. 敏感信息脱敏

**禁止输出的内容**：
- 数据库密码
- 访问令牌
- 私钥
- 完整信用卡号
- 社保号

**需要脱敏的内容**：
- 个人身份信息（PII）：手机号、邮箱、身份证号
- 业务敏感字段：根据配置决定
- SQL 参数：根据策略脱敏

**脱敏示例**：
```
手机号：138****1234
邮箱：m***@example.com
身份证号：110***********1234
```

### 3. Content Security Policy (CSP)

报告应设置 CSP，防止 XSS 攻击：

```html
<meta http-equiv="Content-Security-Policy" content="
  default-src 'none';
  script-src 'none';
  style-src 'unsafe-inline';
  img-src 'self' data:;
  font-src 'self';
">
```

**说明**：
- 禁止执行任何脚本（`script-src 'none'`）
- 允许内联样式（`style-src 'unsafe-inline'`）
- 允许本地图片和 data URI
- 禁止加载外部资源

### 4. 模板与数据分离

- HTML 模板与报告数据必须分离
- 禁止输入内容控制模板结构
- 禁止输入内容执行脚本
- 使用模板引擎渲染报告

### 5. 报告验证

生成报告后应进行安全扫描：
- 检查是否有未转义的特殊字符
- 检查是否有可执行的脚本
- 检查是否有外部资源引用
- 检查是否有敏感信息泄露

---

## 报告质量检查清单

在报告交付前，逐项检查：

- [ ] 所有动态内容都经过 HTML 转义
- [ ] 没有可执行的脚本
- [ ] 没有外部资源引用
- [ ] 没有敏感信息泄露
- [ ] 所有结论都有证据支持
- [ ] 置信度有解释
- [ ] 查询状态准确标记
- [ ] 反证和替代解释已列出
- [ ] 未解决问题已说明
- [ ] 调查限制已披露
- [ ] 证据索引完整
- [ ] 时间统一时区
- [ ] 长内容有折叠处理
- [ ] 报告大小在限制范围内
