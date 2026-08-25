# 运行时架构

v0.5.1 把模型推理与确定性的 PPT 执行分开。五个 Skill 继续拥有内容和设计决策；Runtime 只负责能力发现、路线锁定、有界工具调用、作者适配器和分系统渲染。

## 固定生命周期

`自然语言请求 → 五阶段批准产物 → 一次预检 → 锁定路线 → 一次性收集并缓存来源 → 一次构建 → 最终渲染 QA → 最多一次定向修复 → 交付`

运行中不换路线。后端发生硬失败时结束本次运行；中央配置最多允许从新预检开始一次备选路线重启。

## 模型交互

A—D 是能力分级，不是模型品牌排名。A、B 可直接编排 Runtime；C 输出内部结构化交接，由外部适配器执行；D 有窄工具能力时只调用一次，否则复用 C 的路线。用户不需要手写 JSON。

宿主应把“生成 PPT”的意图绑定到五个 Clayz Skill：新文稿从 Logic 开始，再按批准状态逐层交接。只暴露本地 PowerPoint 自动化、但不经过这些 Skill，不属于符合本架构的接入。

## 依赖层级

1. 通用作者链：Python 3.10+、`python-pptx`、Pillow、PyYAML；不要求宿主模型提供私有演示工具。
2. 最终渲染：Windows 使用一个 PowerPoint COM 进程；macOS/Linux 使用一个 LibreOffice 进程。宿主提供的 Artifact Tool 只是预检时可选的路线。
3. 按需媒体能力：只有 PDF 页面输入或 LibreOffice 的 PDF→PNG 渲染路线才需要 Poppler；只有实际使用 SVG 且当前后端不能原生插入时才需要 SVG 转换器。

仓库自带合同、适配器、验证器、预检逻辑和分系统启动脚本。第三方应用与二进制只有在许可和平台打包单独审查后才可随包分发。

## 本地系统包

运行`python scripts/build_runtime_packs.py --bundle light`可在`dist/`生成一个确定性的轻量插件主包。维护者先用`scripts/fetch_offline_wheels.py`暂存经过审阅的CPython 3.12 wheel，默认构建再生成Windows、macOS和Linux三个独立离线依赖附加包。轻量包不带第三方wheel；离线包只带哈希锁定wheel、安装清单和保留的许可说明。详见[`release-packages.zh-CN.md`](release-packages.zh-CN.md)。
