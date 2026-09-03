# 问题跟踪器：GitHub

本仓库的问题和规格存放在 GitHub Issues 中。所有操作均使用 `gh` CLI。

## 约定

- **创建问题**：`gh issue create --title "..." --body "..."`。多行正文使用 heredoc。
- **读取问题**：`gh issue view <编号> --comments`，使用 `jq` 筛选评论，同时获取标签。
- **列出问题**：`gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'`，并根据需要使用 `--label` 和 `--state` 过滤。
- **评论问题**：`gh issue comment <编号> --body "..."`
- **添加或移除标签**：`gh issue edit <编号> --add-label "..."` / `--remove-label "..."`
- **关闭问题**：`gh issue close <编号> --comment "..."`

从 `git remote -v` 推断仓库；在克隆的仓库中运行时，`gh` 会自动完成此操作。

## 将拉取请求作为分类入口

**将 PR 作为请求入口：否。** _（如果本仓库将外部 PR 视为功能请求，可改为“是”；`/triage` 会读取此标志。）_

设为“是”时，PR 将使用与问题相同的标签和状态流程，并使用对应的 `gh pr` 命令：

- **读取 PR**：使用 `gh pr view <编号> --comments` 查看内容和评论，使用 `gh pr diff <编号>` 查看差异。
- **列出待分类的外部 PR**：运行 `gh pr list --state open --json number,title,body,labels,author,authorAssociation,comments`，仅保留 `authorAssociation` 为 `CONTRIBUTOR`、`FIRST_TIME_CONTRIBUTOR` 或 `NONE` 的项目，排除 `OWNER`、`MEMBER` 和 `COLLABORATOR`。
- **评论、添加标签或关闭**：使用 `gh pr comment`、`gh pr edit --add-label` / `--remove-label` 和 `gh pr close`。

GitHub 的问题和 PR 共用同一编号空间，因此单独的 `#42` 可能指其中任意一种。先运行 `gh pr view 42`，失败后再运行 `gh issue view 42`。

## 当技能要求“发布到问题跟踪器”时

创建一个 GitHub Issue。

## 当技能要求“获取相关工单”时

运行 `gh issue view <编号> --comments`。

## Wayfinding 操作

供 `/wayfinder` 使用。**地图（map）**是一个独立问题，**子项（child）**是地图下的工单。

- **地图**：一个带有 `wayfinder:map` 标签的问题，其正文包含“备注”“目前已作出的决策”和“模糊点”。使用 `gh issue create --label wayfinder:map` 创建。
- **子工单**：作为 GitHub 子问题关联到地图的问题，通过 `gh api` 调用 sub-issues 端点创建关联。如果仓库未启用子问题，则将子项加入地图正文的任务列表，并在子问题正文顶部写入 `Part of #<地图编号>`。标签格式为 `wayfinder:<类型>`，类型可以是 `research`、`prototype`、`grilling` 或 `task`。工单被认领后，将其分配给负责推进的开发者。
- **阻塞关系**：使用 GitHub 原生问题依赖，它是规范且在界面中可见的表示方式。运行 `gh api --method POST repos/<所有者>/<仓库>/issues/<子项>/dependencies/blocked_by -F issue_id=<阻塞项数据库ID>` 添加依赖边。其中 `<阻塞项数据库ID>` 是阻塞问题的数字型**数据库 ID**，通过 `gh api repos/<所有者>/<仓库>/issues/<编号> --jq .id` 获取，而不是 `#编号` 或 `node_id`。GitHub 的 `issue_dependencies_summary.blocked_by` 表示尚未关闭的阻塞项数量，也是当前的执行门槛。如果原生依赖不可用，则在子问题正文顶部使用 `Blocked by: #<编号>, #<编号>`。只有全部阻塞项关闭后，工单才视为已解除阻塞。
- **查询前沿工单**：列出地图下所有未关闭的子项，使用 `gh issue list --state open`，并将范围限制在地图的子问题或任务列表中。排除仍有未关闭阻塞项或已有负责人认领的工单；地图顺序中的第一个合格工单优先。
- **认领**：运行 `gh issue edit <编号> --add-assignee @me`。这是会话中的第一次写操作。
- **解决**：运行 `gh issue comment <编号> --body "<答案>"`，然后运行 `gh issue close <编号>`，最后将上下文指针（gist 及其链接）追加到地图的“目前已作出的决策”部分。
