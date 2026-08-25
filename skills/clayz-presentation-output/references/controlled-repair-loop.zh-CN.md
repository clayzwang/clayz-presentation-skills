# 受控动作与环境反馈合同 v1.1

本合同受 [PPTAgent](https://github.com/icip-cas/PPTAgent) 的“小动作词表、执行历史、失败反馈、定点重试”机制启发，并把这些概念翻译为本工程的 Output 运行机制。它只位于 `ppt-design-package.json` 与 `ppt-art-direction-plan.json` 之下，不产生第二份内容或视觉真源。引用性质与再分发边界见仓库 `provenance/manifest.yaml`。

## 权威顺序

`批准的Logic／Copy／Art Direction → 配置渲染器的技术动作 → 写盘后的PPTX对象与渲染 → Output QA → Supervisor独立观察`

内存状态、工具返回“成功”、单一预览器、自动分数或代理自评都不能覆盖写盘后的对象与真实渲染。环境反馈可以触发技术修复或上游挑战，但不能授权静默改文案、改构图或改母版。

## 记录载体

每次制作生成 `ppt-build-deviation-log.json`，合同版本为 `1.1`。它既保留制作偏差，也记录少量关键观察循环：

- `source_bindings`：批准包、艺术指导计划与当前PPTX的SHA-256；
- `environment_precedence`：固定为 `written-pptx-and-render-over-in-memory-state`；
- `scoring_policy`：固定为 `evidence-not-score`；
- `cycles`：初次写盘观察、定点修复、最终重开观察；
- `deviations`：计划与实际实现之间的技术偏差；
- `challenges`：需要回流Logic、Copy、Art Direction或系统环境的挑战；
- `final_status`：`pass`、`known-risk` 或 `incomplete`。

日志是运行证据，不是新的批准合同。它不得包含未获批准的新文案、替代构图或任意可执行代码。

## 受控动作词表

定点修复只允许以下技术动作：

- `reposition-object`
- `resize-object`
- `reorder-layer`
- `route-connector`
- `adjust-crop`
- `replace-approved-asset`
- `repair-native-chart`
- `repair-native-table`
- `repair-font-encoding`
- `repair-compatibility`
- `deduplicate-media`
- `optimize-raster`
- `remove-duplicate-object`
- `restore-master-inheritance`

每个动作必须绑定 `slide_id`、稳定 `target_ids`、前置条件、执行状态和证据；`authority` 固定为 `output-technical`，`changes_approved_content` 与 `changes_art_direction` 必须为 `false`。需要改变批准基准时，不生成动作，改写入 `challenges` 并交 Supervisor 与用户裁决。

## 循环

1. `initial-render`：写盘并重开当前PPTX，记录对象、字体、兼容、体积和逐页渲染证据；可以没有修复动作。
2. `targeted-repair`：只修受影响页面和对象；必须声明 `repair_of`，不得整稿重写来掩盖局部失败。中央运行预算最多允许一次定向修复循环。
3. 每次修复后重新写盘、重开并渲染受影响页；机器证据与画面解释分开记录。
4. `final-reopen`：从最终写盘文件重开并整稿渲染，绑定最终PPTX哈希；只有这一步可以形成最终 `pass`。

如果某轮执行失败或部分成功，必须进入唯一允许的一轮定点修复、上游挑战或带可见风险继续的决定。失败不能只留在控制台或模型上下文中。重新扫描能力或切换已经锁定的后端不属于修复动作。

## 验证

```powershell
python scripts/validate_build_deviation_log.py `
  ppt-design-package.json ppt-art-direction-plan.json `
  ppt-build-deviation-log.json --pptx final.pptx
```

验证通过只表示运行证据结构完整、动作未越权、哈希可追溯，不表示PPT视觉质量已经通过；最终判断仍由逐页Output QA与Supervisor完成。
