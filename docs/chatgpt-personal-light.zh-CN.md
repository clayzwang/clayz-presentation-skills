# ChatGPT Personal Light

## 0.10.1 同名升级与全局调用

升级包沿用 `clayz-presentation-personal`，可以在普通聊天或 Work 中启用，不依赖
某个 ChatGPT 项目。宿主 Library 根目录通过资源 binding 接入。根 Skill 按请求选择资源检查、
讨论学习或五阶段 PPT 工作，工具能力不足时明确报告当次缺口。

包内新增共享讨论/快照代码及 `scripts/cloud_learning_cli.py`。composer 从原有
host-library 挂载生成 `runtime/native-library-policy.json`，把可选的已确认知识
保存位置约定为该 Library 下的 `_extension/confirmed-learning`。原有 Profile、
两个已声明私人 Provider 及品牌规则不被覆盖；新知识通过同一个 CompositeIndex
作为补充来源参与检索。详见[原生 Library 工作流](../packages/contracts/native-library-workflow.md)。

`stage` 只生成待写入计划，不代表原生 Library 已保存。宿主按计划先保存不可变快照，
再检查并更新 CURRENT，最后重新从 Library 读取文件运行 `verify`。没有真实读写工具
时保留候选稿并报告，不能以临时工作目录替代原生 Library，也不改走 NAS 或 MCP。
本地校验不能代替用户在 ChatGPT 的实际上传和跨会话测试。

本文规定 `scripts/compose_personal_light.py` 生成的私有 ZIP 如何交给 ChatGPT。[OpenAI 官方 Skill 格式](https://learn.chatgpt.com/docs/build-skills)以一个根 `SKILL.md` 为入口，并允许附带 references、assets、scripts 和 UI metadata。composer 因此把唯一 Public Core 的五阶段源码编译成一个自包含 ChatGPT Skill：根 `SKILL.md` 只负责 Supervisor 控制面和内部阶段路由，Logic、Copy、Art Direction、Output、Supervisor 仍是五个职责隔离的内部模块。ChatGPT 已有工具构成身体；ZIP 不依赖五个独立 Skill 自动拼装，也不重复打包本地执行环境。

## 必需控制面与推荐内容结构

本示例使用虚构的 Library 根目录名 `ExampleLibrary`。物理路径属于宿主细节，严禁写进 Skill、index record 或可复用的 Profile 字段。云端私有控制面真正必需的只有 `_extension/providers/<provider>/provider.manifest.json` 及 manifest 声明的索引位置；下面的 `references`、`assets` 和 `cases` 是新资料与渐进迁移的推荐规范结构。源 Profile 保存在本地私有控制面，由 composer 解析后把结果写入 ZIP，不需要再次作为 Library 文件上传。

```text
ExampleLibrary/
├── _extension/
│   └── providers/
│       └── <provider-id>/
│           ├── provider.manifest.json
│           └── index/
│               └── records.jsonl
├── references/
│   ├── logic/
│   ├── copy/
│   ├── art-direction/
│   ├── output/
│   └── supervisor/
├── assets/
│   ├── masters/
│   ├── brand/
│   └── fonts/
└── cases/
    ├── admitted/
    └── rejected/
```

索引 payload ref 只使用以 `library://<profile-namespace>/` 为根的逻辑 URI。Profile 的 `chatgpt-personal` mount 在本示例中把这个逻辑根绑定到虚构宿主根目录 `ExampleLibrary`。

第一次测试前不必移动已有私有资料。只要已准入 index record 通过正确的逻辑 URI 指向当前 Library 位置，旧目录可以继续使用。移动或改名时，应同步更新 source URI 与 payload URI，重建 `records.jsonl` 和 `provider.manifest.json`，再把两者替换到稳定控制面位置；禁止先移动文件却保留陈旧索引。

## 在本地生成

真实 Profile 和 Provider manifest 必须放在公共仓库之外：

```bash
python scripts/compose_personal_light.py <private-profile.json> \
  --provider-manifest <private-provider.manifest.json>
```

默认输出写入 `dist/private/`；该目录不进入公共 release scan，也不应被 Git 跟踪。可直接上传到 ChatGPT Skills 的 ZIP 只含一个根 `SKILL.md`，并包含 `agents/openai.yaml`、唯一 Public Core、公共 Provider manifest/index、五个内部阶段模块、一份生成的 resolved config、`runtime/personal-extension.json`、外部 `runtime/runtime-lock.json`、`runtime/skill-mount-contract.json`、运行时预检合同 1.3、监督报告合同 3.3 和成对发布器。外部 pack lock 锁定全部必选 Provider 的精确集合与 snapshot，防止 runtime 与 config 被同时缩减后自洽通过。ZIP 不包含 `.codex-plugin/plugin.json`、嵌套 `SKILL.md`、本地适配器、系统包、源 Profile、源私有 manifest、私有 JSONL 索引、附件、母版、字体或案例。

单Skill上传包还会删除 `.github`、README、Changelog、知识脚手架和其他仓库维护文件，并只保留一份阶段参考树。五个内部 `stage.md` 通过相对路径读取 `skills/<stage>/references/` 中的唯一副本，不再把同一参考重复写入 `references/stages/<stage>/references/`。这是上传体积与文件数优化，不改变Public Core、Provider快照或阶段方法。

composer只裁剪不属于执行依赖的平行语言文档：保留当前语言合同、公共Capability Index引用，以及组件版本读取器共享依赖表中的全部文件。英文Copy合同含有代码实际读取的版本标记，必须与中文阅读版本同时保留，不能把翻译重命名成英文源文件。现有runtime lock记录除自身以外全部交付文件的SHA-256。打包后解压最终ZIP，以`--mode archive`严格检查全部文件集合及哈希；安装后使用默认`--mode installed`，将ChatGPT会再生成的`agents/openai.yaml`、可能由宿主管理的`assets/icon.svg`及额外文件记录为非阻断观察，不把它们当成运行时权威。其余声明文件、必需依赖覆盖、实际组件版本和私人配置锁继续严格检查；任务输出应放在Skill目录之外。192成员仅是保守上传目标，不是已证明的平台限制，更不能成为裁掉依赖的理由。

仓库和 Codex 插件仍以五个独立 Skill 作为源码与运行结构。只有 ChatGPT Skills 上传适配器把它们编译为一个发布单元；这不会新增公共核心，也不会合并五阶段的责任边界。若确实要生成 marketplace 插件形态，可显式传入 `--artifact-kind plugin --plugin-name clayz-presentation-skills-personal`，该包不得再交给 ChatGPT Skills 上传器。

演示文稿任务开始时，Supervisor 会盘点已挂载运行时、任务输入、所有者 Library、公共 Index、品牌资产、主机能力和字体，并在 Logic 前向用户说明发现与选用情况。所有者学习来源清单根据该次盘点在任务目录生成，再交给 `scripts/materialize_owner_index.py`；该清单及原始字节不会进入公开仓库。

在盘点之前，根 Skill 运行 `scripts/component_version_guard.py --mode application`，离线验证安装包自身组件一致性，并把新鲜报告交给运行时预检绑定。GitHub、Codex 与 ChatGPT 版本不同、网络不可用、开发候选验收日期过期均不阻止制作和交付；联网发布核验仅由开发端显式执行。owner-personal 模式还必须解析一个可跨任务持久化的私有学习状态根。某版本首次运行时，根 Skill 调用 `scripts/bootstrap_owner_learning.py`，真实物化并索引已准入的知识、模板、规范和方法，执行检索验证并把独立学习审计交给用户；后续任务只复用。若 ChatGPT 宿主不能把该状态持久保存到 Library 或等价 owner-private 存储，必须在 Logic 前报告 `version-private-learning-state-unavailable`，不能每次重新学习来伪装满足要求。

## 上传和更新规则

1. 上传 composer 默认生成的单 Skill ZIP；不要把 marketplace 插件 ZIP 或五个分拆 Skill 交给 ChatGPT Skills 上传器；
2. 根目录必须只有一个 `SKILL.md`，`runtime/skill-mount-contract.json` 必须枚举并验证五个内部阶段模块；
3. 不要在 ChatGPT 中直接修改生成的 runtime 或 resolved config；应修改源 Profile 后重新生成；
4. 新增参考时，只更新 Library 附件、已准入 index record 和稳定位置上的 Provider manifest；Profile 或 Provider 清单不变时无需重新生成 cloud light；
5. 替换包后，用新会话做验收；
6. 旧五个自用 Skill 只在新单 Skill 验收期间作为回滚。直接调用、隐式调用、前置环境与资源简报、五阶段交接、必需资产失败关闭、PPTX 与完整审计报告成对交付、公共 fallback 全部通过后，再禁用或删除；
7. 过去用于维护 GitHub PPT 流程的 ChatGPT Project 不再是运行依赖，清点其独有文件后可以归档。

## 长上下文、可见性与断点续跑

ChatGPT 自用版不得把五阶段的完整 JSON、检索正文、日志和审计报告反复塞回对话。根 Skill 在首次长扫描前先发送一条简短可见进度；预检及每个阶段完成后，只报告“已过门禁、下一阶段、阻塞或延后验收”，完整证据留在任务文件中。模型一次只加载根规则、当前阶段模块、当前语言的必要引用和已批准产物的路径／SHA-256 摘要；上一阶段的完整产物按需从文件读取，不在提示或聊天中重述。长资料按与当前判断相关的片段或分块读取，选中记录也不得默认整篇载入。

这里压缩的是重复运输和重复执行，不是Logic的思考。每阶段默认先做一次聚焦检索，只有关键问题仍未解决时才增加回执，候选／入选预算按整个阶段累计。Logic可充分使用私人库中的事实、方法与反例，但必须独立完成“在哪里、去哪里、怎么去”的综合判断。除非用户明确同时省略，封面与尾页始终作为首尾叙事角色保留，正文页数与总页数分开计算。Storyline本身按当前母版的规定填写和定位；其下方较小的辅助文字不是必填，没有独立信息价值时应完全留空。

预检和每个阶段完成后，任务根刷新一个小型 `run-context-checkpoint.json`。它只记录运行与请求哈希、已完成／下一阶段、权威产物路径及哈希、阻塞或延后项和简短需求摘要；它是派生的续跑索引，不是新的合同真源，也不得包含私人正文或思维链。若当前对话已经出现整稿失败、重复大生成或宿主上下文／压缩警告，先校验该检查点并从 `next_phase` 续跑，不重做已经通过哈希验证的阶段。确实无法安全加载下一阶段时，应在开始该阶段前停在可恢复检查点，并让用户在新对话中携带检查点和权威产物继续；这属于上下文边界，不把整次演示任务判为失败。

成对交付目录一旦验证完成，聊天回复必须“交付优先且短”：先给 PPTX 与监督报告，再写验证状态及少量实质性延后项，不得把完整监督报告复制进聊天。这样即使移动端或长会话显示不稳定，已生成文件、验证证据和续跑位置仍然可恢复。

最终云端运行形态是“单一 ChatGPT Skill 发布入口 + 唯一 Cloud Public Light 脑 + 五个内部阶段模块 + ChatGPT 工具身体 + Personal Extension Profile + 私有 Library/索引记忆”。云端宿主的实际文件和工具能力可能与本地 Codex 不同；mount 只证明资料可发现，不代表某项工具或字体一定可用。Supervisor 必须先打开生命周期记录，保存规范化当前请求的原始字节，签发新鲜运行挑战及任务根签发记录，解析 `config/personal-extension-resolved.json`，再用同一任务字节在 Logic 前且只执行一次预检。预检绑定脚本签发的 run ID、任务哈希、nonce、task-root 摘要、规范签发/消费回执和配置实际哈希；复制或改名挑战不能重放，任务要求只能追加。“可用”的宿主能力必须绑定同一挑战并由经过哈希校验的 inventory 回执支持，但仍是 `host-declared-unverified`，只能形成 provisional/attemptable 路线，不能形成 ready。该路线可锁定尝试一次，只有最终 PPTX、对象与渲染被独立验证后才可交付。无法物化并在适用阶段实际选用全部必选私人 Provider，或既无 ready 也无 attemptable 制作/渲染路线时必须 fail closed。PowerPoint/WPS 等目标应用无论有无都要扫描，但其原生重开能力属于输出后验收观察，不属于开工硬条件；缺失时在最终报告中记录 `deferred` 并限制兼容性声明。最终交付必须由 `scripts/publish_supervised_pair.py` 物化，同时包含 PPTX 与 `ppt-supervision-report.json`，并由 `delivery-manifest.json` 证明二者成对；缺一不得标记完成。

每个任务开始时，按下面两步建立新鲜绑定。签发阶段还会生成 `.clayz-run-challenges/<run>.issued.json`，扫描阶段通过 `.clayz-run-challenges/consumed/<challenge-sha>.json` 唯一消费。扫描必须再次传入签发时的同一份不可变任务请求；挑战被复制/复用、缺少签发记录、任务根变化或任务字节变化都要 fail closed。若宿主声明演示工具可用，attestation 必须复述 challenge 字段，并通过 SHA-256 回执指向任务级 `host-tool-inventory/1.0` JSON；形成的路线仍为 provisional，直至最终产物验证通过。不要把瞬时能力清单写进 Profile 或 Library 索引。

```bash
python scripts/runtime_preflight.py --issue-challenge \
  --task-request <canonical-task-request.txt> --output <run-challenge.json>
python scripts/runtime_preflight.py --challenge <run-challenge.json> \
  --task-request <canonical-task-request.txt> \
  --component-version-report <component-version-report.json> \
  --host-capabilities <host-capability-attestation.json> \
  --output <runtime-preflight.json>
```
