# 运行时路由合同

## 一次扫描，一条路线

进入 Logic 前，由根 Supervisor 保存规范化任务请求的原始字节，先用 `../../../scripts/runtime_preflight.py --issue-challenge` 签发新鲜运行挑战，再用同一任务字节和挑战执行且只执行一次能力扫描。签发与消费分别写入同一任务根下按 run/challenge 锁定的两份规范台账；预检库会重读两份文件并核对其字节哈希，因此复制或改名挑战文件不能重放，移动到另一任务根也会被拒绝。Output 只能消费同一份任务级 `runtime-preflight.json`，不得再次扫描。报告必须绑定脚本签发的运行 ID、任务请求 SHA-256、nonce、task-root SHA-256、签发/消费回执哈希，以及实际 resolved config 文件的 SHA-256；`selected_route.locked=true` 是执行不变量。

运行中不得重新发现工具、重新选择依赖或切换后端。锁定后端发生硬失败时，应结束本次运行；最多允许重新从预检开始一次，并从已报告的备选路线中选择。重新预检属于新运行，不是中途换路。

## 路线门槛与目标应用验收分离

`renderer.required_capabilities` 只描述能够制作、写盘、检查和渲染 PPTX 的路线硬条件。`renderer.target_applications` 描述希望观察的兼容性目标，不得把 `powerpoint-reopen-render`、`wps-reopen-render` 等逐应用验收能力自动并入路线硬条件。预检必须逐项记录所有目标应用，无论其能力存在还是缺失；“可用”的宿主声明必须绑定同一 run/task/nonce/challenge，并附带经哈希校验的结构化 inventory 回执，但仍只属于 `host-declared-unverified`，只能产生 `provisional`/`attemptable` 路线，不能把路线写成 `ready`。Output 可按锁定路线尝试一次，只有最终 PPTX、对象与渲染校验通过才可交付。输出后，已执行目标记为 `pass`/`fail`，可用但未执行记为 `not-selected`，不可用记为 `deferred`，并全部进入最终 Supervisor 审计。

预检必须在 `target_application_checks` 中逐一记录每个目标应用的 `available` 或 `unavailable`，并固定 `blocks_authoring=false`。任何“可用”的宿主能力声明还必须携带同一运行 ID、实测来源、观察时间和证据引用；未绑定声明不可信。Output 写盘后，对可用且入选的应用执行重开渲染并记录 `pass` 或 `fail`；可用但未入选的应用记录 `not-selected`；不可用的应用记录 `deferred`。Supervisor 将这些事实和证据写进最终审计报告，用于限制兼容性声明和后续归因，而不是据此阻断 Logic。

`required_capabilities` 必须取绑定 resolved config 与本任务追加要求的并集。调用方只可追加要求，不得借覆盖参数删除 Personal Extension 已声明的要求。

## 不依赖宿主模型的基础链

基础作者链由公开 render-manifest 合同和公开 `python-pptx` 适配器组成。宿主模型不直接编写坐标；它只提交已经批准的语义产物，确定性的 Output 层消费解析后的 manifest。宿主若提供 Artifact Tool 且满足同一合同，可以在预检时选中，但它不是基础链的必要条件。

## 能力分级

分级描述交互能力，不按模型品牌划分，也不只按模型大小划分。

| 级别 | 交互路线 |
| --- | --- |
| A | 具备工具调用、结构化输出和视觉检查；可直接编排并完成最终视觉审查。 |
| B | 具备工具调用和结构化输出；可直接编排，但视觉 QA 由外部工具或人工完成。 |
| C | 只能输出结构化文本／JSON；由外部适配器调用同一条锁定运行链。 |
| D | 受限或小模型；有窄工具调用能力时直接调用一次，否则复用 C 类适配路线。 |

用户始终用自然语言交互。`runtime-preflight.json`、render manifest 等 JSON 是内部交接合同，不要求用户手写。

## 有界执行

预算只从中央配置读取。常规路线只做一次能力扫描、一次来源收集、一次写盘、至多一个常驻 Office 进程和一次整套最终渲染。发现技术缺陷时，最多进行一次定向修复、一次额外写盘和一次额外整套渲染。技术修复不得重写已经批准的 Logic、Copy 或 Art Direction。

## 系统运行包与 PDF

使用 common 包加且仅加一个操作系统包。Windows 优先使用单一常驻 PowerPoint COM 进程渲染；macOS 和 Linux 优先使用一个 LibreOffice 进程。PDF 页面能力按需加载；只有输入包含 PDF 页面，或锁定的 LibreOffice 路线需要先把 PPTX 转 PDF 再转 PNG 时，才要求 Poppler。
