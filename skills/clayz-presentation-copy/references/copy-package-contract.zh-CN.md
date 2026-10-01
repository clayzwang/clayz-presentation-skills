# Copy 内容包 3.1

遵循[完整故事与页面交接](../../../packages/contracts/story-visual-handoff.zh-CN.md)。Logic 提供完整 story 和锁定的页面安排；Copy 决定具体文字、剪裁、内容分组及打标，Art Direction 继续视觉打标，Output 实施。

保留根包身份、version、配置、acceptance_contract、resource_inventory、story 和 logic_layer，绑定真实 logic_artifact。保留阶段校准和检索回执，copy_layer.logic_version 等于根 version；pagination_owner 为 logic，story_sha256 绑定完整原始故事，chapter_order 不变。用 semantic_preservation_review 记录对数字、限定条件和含义的实际检查。

每页的 slide_id 与 Logic 页序一致。每个 copy_unit 保留 copy_id、text、role、text_mode、source_story_ids、parent_copy_id、sibling_group_id、logic_level、order、render_separately、merge_with_children、intentional_line_breaks。copy_id 全稿唯一；来源限定在本页 story 分配内；父级引用本页其他单元且无环，组标记可为 null。logic_level 描述 Copy 自建层级，不要求与 Logic 节点对齐。

render_separately 为 true、merge_with_children 为 false，表示每个 copy_id 可独立追踪，不强制单独文本框或卡片。order 从 1 连续排序。intentional_line_breaks 记录有效字符位置，措辞和断句由 Copy 决定。title_copy_id、可选 storyline_copy_id 及 footnote_copy_ids 引用本页可见文字。必要解释可以是完整句子或段落，不强制平行句式。

旧 source_logic_node_ids、node_copy_map 不是新任务的必填项。Copy 可以自行建立消息树；Art 用 Copy 的层级和组标记承接。页数、顺序、页面职责、主张或证据变化回 Logic；措辞和分组变更由 Copy 完成，并更新下游绑定。不主动生成演讲备注或附录；已有或明确要求的备注可读、可追溯。历史 2.4 和 3.0 包仍走各自兼容校验。
