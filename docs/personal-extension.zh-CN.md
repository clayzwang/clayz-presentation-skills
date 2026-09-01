# Personal Extension Profile

v0.5.2 奠定了既有五阶段之前的可选所有者私有扩展点。它不增加第六个 Skill，不复制任何阶段，也不新建第二套检索引擎。公共资料、公共 Library 和公共索引仍是必须规整并可用的组成部分；暂缓的是公共资料持续学习、社区汇聚、自动更新和跨来源融合的方法。

```text
GitHub 公共源
  -> 唯一 Public Core + 公共 Library + 公共 Provider manifest/index
  -> Cloud Public Light / Local Public Light

Cloud Public Light（脑）
  + 私有 Personal Extension Profile
  + 私有 Library Provider（记忆）
  + ChatGPT 宿主工具（身体）
  -> 一份已解析的 Personal Extension Runtime
  -> Logic -> Copy -> Art Direction -> Output -> Supervisor
```

## 三份契约

公共仓库定义三份通用契约：

1. `personal-extension-profile.schema.json`：验证私有、人工维护的 Profile；
2. `provider-manifest.schema.json`：用同一契约描述随包公共 Provider 与所有者私有 Provider；
3. `personal-extension-runtime.schema.json`：验证 composer 生成的宿主专用运行信封。

检索仍然只走现有的 `index-record`、retrieval request/receipt、`IndexProvider` 和 `CompositeIndex`。`resource-inventory.schema.json` 增加 Logic 前盘点和用户简报，`index-execution-evidence.schema.json` 则证明任务级所有者来源物化与各阶段回执覆盖。所有者学习清单根据该次盘点作为运行时输入生成，不是仓库文件。`catalog/provider-manifest.json` 与 `catalog/records.jsonl` 是公共 Provider 的规范控制面与唯一索引真源；`knowledge/index/search-cache.json` 只是本地 Library 工具生成的派生缓存。私有记录保留独立 `provider_id`、哈希、权限、人工准入状态和 `never_copy` 边界。公共仓库不得包含真实私有 Profile、manifest、索引、附件、母版、字体、品牌值或原生路径。

## 覆盖策略

策略由公共 resolver 决定，私有 Profile 不能自行声明更宽松的策略，也不能覆盖 sealed 字段。

- `replace` 只允许修改明确的演示文稿选择，例如 locale、主题身份、母版逻辑 URI、颜色、有序字体栈、部分布局值和交付档位；
- `theme.typography.font_validation` 把规范字体名及其等价别名建模为一个字体身份；别名只用于解析已安装名称，不能在 `primary_fonts` 中成为额外回退位，Latin 与 East Asian PPTX 字体字段只写该身份的 `pptx_family`；
- `append_unique` 只能追加能力、目标应用、后端或版式角色列表，不能删除公共基线；
- `stricter_only` 只能提高字号阈值或打开验证门禁，不能降低阈值或关闭已有门禁；
- workflow、namespace、版本、公开署名、路线预算、学习准入和核心合同字段全部 sealed。

每个生效的覆盖项都会写入 origin map。生成的 runtime 同时绑定 resolved config 哈希和自身确定性 lock digest；Personal 组合包还会写出一份外部 runtime-pack lock，绑定上述两个摘要及全部 `required: true` Provider 的精确排序集合。验证时三者缺一不可，不能通过同步缩减 runtime/config 并重算内部摘要来删掉必选 Provider。

## 逻辑 Library 挂载

Skill 和私有索引记录只能保存 `library://<namespace>/...`。真实路径只存在于 composer 选择的宿主 binding 中：

```json
{
  "mount_id": "private-library",
  "logical_root": "library://example-presentation/",
  "bindings": {
    "local": {"adapter": "filesystem", "root": "${CLAYZ_PRESENTATION_LIBRARY_ROOT}"},
    "chatgpt-personal": {"adapter": "host-library", "root": "PPT"}
  }
}
```

同一个逻辑 URI 可以在本地解析成文件，也可以在 ChatGPT 中解析成 Library 项目，不需要修改阶段方法或索引记录。公共 Provider 在两个 Light 中都使用不可变的 `bundle://public-library/` mount。binding 不允许越出根目录。云端 composer 只选择 `chatgpt-personal` binding，并且不会把私有 Provider 索引或附件复制进插件 ZIP。

## 私有索引生命周期

每次演示任务开始先运行组件版本门禁，核对官方最新 Release 与当前 Public Core、配置、运行时及各阶段合同，并由 Supervisor 把版本表展示给用户。Personal Runtime 还声明 `version_learning` 政策：宿主必须提供仓库外、可跨任务持久化的 owner-private 状态根，任务临时目录不能冒充。

某个 Public Core 版本首次运行时，所有者学习清单中的每个来源都要声明 `knowledge_kinds`，整体至少覆盖私人知识、模板、规范和方法。宿主物化已准入原始字节后，`scripts/bootstrap_owner_learning.py` 计算来源集合摘要、调用现有 Index 物化器、执行四类检索探针，并生成独立 `version-private-learning-audit.json` 和 Markdown 简报。后续任务只复核来源、审计和索引哈希并复用。来源在同一核心版本下发生变化时停止，不自动重学；需要通过新版本或单独迁移治理处理。

在公共仓库之外维护已准入的私有 IndexRecord，然后用共享契约生成 manifest：

```bash
python scripts/build_provider_manifest.py \
  --provider-id example.private-library \
  --visibility owner-private \
  --records <private-path>/records.jsonl \
  --index-uri library://example-presentation/_extension/providers/private/index/records.jsonl \
  --output <private-path>/provider.manifest.json
```

把 `records.jsonl` 和 `provider.manifest.json` 放在 Profile 声明的稳定逻辑位置。每个任务只读取一次私有 manifest，并把当时的 snapshot 锁进五阶段共享的检索证据。因此，增加一份已准入参考只需要更新私有索引和 manifest，不需要修改公共插件。只有 core 版本、Profile 规则、宿主 mount 或 Provider 清单变化时，才重新生成云端 personal runtime。

## 失败与演进边界

- 没有生成 runtime 时，五个 Skill 读取 `config/default.json` 和随包公共 Provider；
- 可选私有 Provider 不可用时，显式记录 public-core fallback；
- 任务所需的必选 Provider、母版、字体或品牌资产不可用时，必须 fail closed；
- `renderer.required_capabilities` 只追加制作路线真实需要的能力；PowerPoint/WPS 等逐应用原生重开验收通过 `target_applications` 和预检观察管理，不得追加为 Logic 前硬条件；
- owner-personal 模式下，预检必须读取生成后的 resolved config，根据规范化任务请求原始字节签发新鲜挑战并写入规范任务根签发台账；唯一一次扫描必须再次提交同一字节，以排他方式写入规范任务根消费台账，重读两份台账并绑定其文件哈希与配置原始 SHA-256；任务级要求只能追加。调用方自选 run/task 值、缺失或仅在内存伪造的回执、复制/重放/跨任务根挑战、退回公共 `config/default.json` 或缩减 Personal Extension 要求都属于集成失败；
- runtime pack lock 与任务 Index 证据必须为每个必选私有 Provider 保留非空 snapshot；每个必选 Provider 还必须在其适用治理阶段被 finalized receipt 实际选中，并复用同一个 Provider snapshot lock。仅在共享 snapshot 中列名不算完成对接；
- 最终交付只能由 `scripts/publish_supervised_pair.py` 物化；发布器会用同一 resolved config 和预检重新验证审计报告，再生成 PPTX/报告双文件及清单；
- 私有记录不能绕过权限、哈希、准入、receipt 或物化检查；
- Provider 发现和 snapshot 锁定只在 Logic 前发生一次，后续阶段复用同一任务锁；
- 公共 Provider manifest 显式把 `continuous_learning`、`community_aggregation`、`automatic_update` 和 `cross_source_fusion` 四种方法标为 `deferred`，但现有公共资料本身没有被延期或禁用。

Task Overlay、远程 MCP Provider 和私有 Library 自动摄取也明确延期。
