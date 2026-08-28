# 运行时架构

v0.6.0 保留 v0.5.2 对演示推理、受治理检索与执行的分离，并把 Logic 前的资源盘点升级为强制步骤。唯一 Public Core 与随包公共 Provider 在所有目标中构成同一个脑；本地适配器执行 Local Light 路线，ChatGPT 宿主工具构成 Cloud Light 的身体。五个 Skill 继续拥有内容和设计决策；Runtime 负责资源与能力发现、路线锁定、有界工具调用和宿主边界。

## 固定生命周期

`自然语言请求 → 五阶段批准产物 → 一次预检 → 锁定路线 → 一次性收集并缓存来源 → 一次构建 → 最终渲染 QA → 最多一次定向修复 → 交付`

运行中不换路线。后端发生硬失败时结束本次运行；中央配置最多允许从新预检开始一次备选路线重启。

## 模型交互

A—D 是能力分级，不是模型品牌排名。A、B 可直接编排 Runtime；C 输出内部结构化交接，由外部适配器执行；D 有窄工具能力时只调用一次，否则复用 C 的路线。用户不需要手写 JSON。

宿主应把“生成 PPT”的意图绑定到五个 Clayz Skill：新文稿从 Logic 开始，再按批准状态逐层交接。只暴露本地 PowerPoint 自动化、但不经过这些 Skill，不属于符合本架构的接入。

云端宿主先检查当前真实可用的演示能力，再向预检传入任务级 `host_capabilities` 声明；只有这样，Runtime 才能把 `native-presentation-tool` 锁定为作者／渲染路线。该声明只是当前宿主能力证据，不是随包工具，也不是永久可用承诺。

## 依赖层级

1. 通用作者链：Python 3.10+、`python-pptx`、Pillow、PyYAML；不要求宿主模型提供私有演示工具。
2. v0.6.0 本地发布的最终渲染：Windows 使用一个 PowerPoint COM 进程。Cloud Public Light 可在预检时选择宿主提供的演示或 Artifact Tool 路线。其他本地操作系统路线不是本版发布承诺。
3. 按需媒体能力：只有 PDF 页面输入或 LibreOffice 的 PDF→PNG 渲染路线才需要 Poppler；只有实际使用 SVG 且当前后端不能原生插入时才需要 SVG 转换器。

仓库自带合同、适配器、验证器、预检逻辑和分系统启动脚本。第三方应用与二进制只有在许可和平台打包单独审查后才可随包分发。

## 公共 Light 目标与本地系统包

运行`python scripts/build_runtime_packs.py --bundle light`可在`dist/`生成确定性的 Cloud Public Light 与 Local Public Light。两者绑定相同的 `public_core_sha256` 和公共 Provider snapshot。Cloud Light 因 ChatGPT 已提供工具而排除本地适配器与系统包；Local Light 保留本地执行路线。维护者用`scripts/fetch_offline_wheels.py --platform windows`暂存经过审阅的 CPython 3.12 wheel，v0.6.0 只生成 Windows 离线依赖附加包。两个 Light 都不带第三方 wheel，本版不生成 macOS、Linux 或 iOS 发版包。详见[`release-packages.zh-CN.md`](release-packages.zh-CN.md)。
