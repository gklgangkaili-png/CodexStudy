# 使用 MaaFramework 作为执行内核

本项目采用 MaaFramework 负责 Windows 窗口截图、传统视觉识别、任务 Pipeline 与键鼠执行，自研示教录制、示教分析、人工校准及 Pipeline 生成层。首版不使用通用视觉大模型，因为 MaaFramework 已覆盖实时执行所需的确定性能力，而视觉模型会增加资源消耗、延迟与不可预测性；未来仅在有明确收益时作为可选插件评估。
