# 领域文档

本文件说明工程技能在探查代码库时应如何使用本仓库的领域文档。

## 探查前读取以下内容

- 根目录下的 **`CONTEXT.md`**；或者
- 如果根目录存在 **`CONTEXT-MAP.md`**，则读取它。该文件会指向各个上下文的 `CONTEXT.md`，应读取与当前主题相关的每一份文档。
- **`docs/adr/`**：读取与即将处理的区域相关的 ADR。在多上下文仓库中，还应检查 `src/<上下文>/docs/adr/` 中限定于该上下文的决策。

如果其中任何文件不存在，**静默继续**。不要指出文件缺失，也不要预先建议创建。`/domain-modeling` 技能（可通过 `/grill-with-docs` 和 `/improve-codebase-architecture` 使用）会在术语或决策真正得到明确时按需创建这些文件。

## 文件结构

单上下文仓库（适用于大多数仓库）：

```text
/
├── CONTEXT.md
├── docs/adr/
│   ├── 0001-event-sourced-orders.md
│   └── 0002-postgres-for-write-model.md
└── src/
```

多上下文仓库（以根目录存在 `CONTEXT-MAP.md` 为标志）：

```text
/
├── CONTEXT-MAP.md
├── docs/adr/                          ← 系统级决策
└── src/
    ├── ordering/
    │   ├── CONTEXT.md
    │   └── docs/adr/                  ← 上下文专属决策
    └── billing/
        ├── CONTEXT.md
        └── docs/adr/
```

## 使用术语表中的词汇

当输出中需要命名领域概念时，例如问题标题、重构建议、假设或测试名称，应使用 `CONTEXT.md` 中定义的术语。不要改用术语表明确避免的同义词。

如果术语表尚未包含所需概念，这就是一个信号：要么正在创造项目并未使用的语言，此时应重新考虑；要么确实存在领域文档缺口，此时应记录下来，交由 `/domain-modeling` 处理。

## 标明与 ADR 的冲突

如果输出与已有 ADR 冲突，应明确指出，而不是静默覆盖：

> _与 ADR-0007（事件溯源订单）冲突，但值得重新讨论，因为……_
