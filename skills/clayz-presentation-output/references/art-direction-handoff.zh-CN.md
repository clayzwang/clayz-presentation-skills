# 艺术指导交接合同

## v0.17.0 current contract

New runs follow [Story and visual handoff](../../../packages/contracts/story-visual-handoff.md). Logic owns a complete narrative; Copy owns pagination; Art Direction locks full-deck images and visual specifications. The fields below describe the legacy page projection consumed by existing validators/renderers. In package 3.0 Copy creates that projection; it is not the original Logic artifact. Legacy coordinate-free restrictions apply to reusable patterns, not the task visual specification.

## Legacy / compatibility field reference

Output只接受合同1.3、状态 `art-direction-approved` 的 `ppt-art-direction-plan.json`。

## 未经裁决不得改变的基准字段

- 整稿：视觉命题、材料路线、第一印象、轮廓序列、密度序列、主媒介序列、母题序列、系列组与语义留白页；
- 逐页：第一视觉、构图理由、区域职责、面积比例、主骨架、轮廓、主媒介、密度、阅读动线；
- 接口：copy_id映射、父子目标、语义布局树、样式token、媒介对象要求、语义轴、识别标准、字号下限、偶数字号、图表标签与连线语义、系列行为、持久元素、递进变化、允许变化、语义留白和持续导航；
- A/B：入选候选、淘汰候选与淘汰理由；
- 参考：每个案例的用途和不可复制边界。

## Output可以决定

- 12列区域内的精确x/y/w/h；
- 同一锁定构图内的间距、内边距、线宽和对象层级；
- 连接器绕线、图片裁切和表格列宽；
- 图表兼容性遮罩、中央配置所列目标应用之间的差异修复；
- 不改变面积与权重的光学对齐。
- 在锁定区域内部选择绝对、相对或混合坐标实现；相对布局只可吸收换行与同级模块数量变化，不得改变固定外框、区域职责、面积权重、阅读顺序或语义留白。
- 把 `semantic_layout_tree` 落成可辨认的对象父子分组、层级、阅读顺序和形状语义；树不取代 `area_plan` 的几何真值，也不取代 `copy_unit_map` 的文字与目标真值。不得因为实现方便把层级树展平成同级浅框。
- 在同一系列合同内复用已锁定持久元素的精确坐标、尺寸、样式和对象层级；不得把“复用”扩大到未进入系列的页面。

## 回流

- 要换媒介、轮廓、主骨架、区域、动线、系列骨架、母题、语义留白或持续导航：回Art Direction；
- 要删字、改字、改断句：回Copy；
- 要改关系、层级、数字或页序：回Logic；
- 如果满足请求需要改变上游基准或用户明确的“不满足就不交付”条件：停止该项变更，记录冲突、证据、预期漂移和可行替代方案，交 Supervisor 汇总并取得必要的用户决定。成品质量缺陷在绑定完整时可以作为审计发现继续交给 Auditor。

所有偏差写入 `ppt-build-deviation-log.json`。若字段 `changes_art_direction=true`，必须同时有Art Direction新版本和用户批准依据；不得只在偏差日志中自我批准。挑战本身不修改基准，用户裁决后才形成新版本。
