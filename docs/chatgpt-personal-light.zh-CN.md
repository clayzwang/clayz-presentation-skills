# ChatGPT Personal Light

本文规定 `scripts/compose_personal_light.py` 生成的私有 ZIP 如何交给 ChatGPT。[OpenAI 官方 Skill 格式](https://learn.chatgpt.com/docs/build-skills)以一个根 `SKILL.md` 为入口，并允许附带 references、assets、scripts 和 UI metadata。composer 因此把唯一 Public Core 的五阶段源码编译成一个自包含 ChatGPT Skill：根 `SKILL.md` 只负责 Supervisor 控制面和内部阶段路由，Logic、Copy、Art Direction、Output、Supervisor 仍是五个职责隔离的内部模块。ChatGPT 已有工具构成身体；ZIP 不依赖五个独立 Skill 自动拼装，也不重复打包本地执行环境。

## 必需控制面与推荐内容结构

使用一个名为 `PPT` 的 Library 根目录。物理路径属于宿主细节，严禁写进 Skill、index record 或可复用的 Profile 字段。云端私有控制面真正必需的只有 `_extension/providers/<provider>/provider.manifest.json` 及 manifest 声明的索引位置；下面的 `references`、`assets` 和 `cases` 是新资料与渐进迁移的推荐规范结构。源 Profile 保存在本地私有控制面，由 composer 解析后把结果写入 ZIP，不需要再次作为 Library 文件上传。

```text
PPT/
├── _extension/
│   └── providers/
│       └── private/
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

索引 payload ref 只使用以 `library://<profile-namespace>/` 为根的逻辑 URI。Profile 的 `chatgpt-personal` mount 把这个逻辑根绑定到 `PPT`。

第一次测试前不必移动已有私有资料。只要已准入 index record 通过正确的逻辑 URI 指向当前 Library 位置，旧目录可以继续使用。移动或改名时，应同步更新 source URI 与 payload URI，重建 `records.jsonl` 和 `provider.manifest.json`，再把两者替换到稳定控制面位置；禁止先移动文件却保留陈旧索引。

## 在本地生成

真实 Profile 和 Provider manifest 必须放在公共仓库之外：

```bash
python scripts/compose_personal_light.py <private-profile.json> \
  --provider-manifest <private-provider.manifest.json>
```

默认输出写入 `dist/private/`；该目录不进入公共 release scan，也不应被 Git 跟踪。可直接上传到 ChatGPT Skills 的 ZIP 只含一个根 `SKILL.md`，并包含 `agents/openai.yaml`、唯一 Public Core、公共 Provider manifest/index、五个内部阶段模块、一份生成的 resolved config、`runtime/personal-extension.json`、外部 `runtime/runtime-lock.json`、`runtime/skill-mount-contract.json`、运行时预检合同 1.2、监督报告合同 3.3 和成对发布器。外部 pack lock 锁定全部必选 Provider 的精确集合与 snapshot，防止 runtime 与 config 被同时缩减后自洽通过。ZIP 不包含 `.codex-plugin/plugin.json`、嵌套 `SKILL.md`、本地适配器、系统包、源 Profile、源私有 manifest、私有 JSONL 索引、附件、母版、字体或案例。

仓库和 Codex 插件仍以五个独立 Skill 作为源码与运行结构。只有 ChatGPT Skills 上传适配器把它们编译为一个发布单元；这不会新增公共核心，也不会合并五阶段的责任边界。若确实要生成 marketplace 插件形态，可显式传入 `--artifact-kind plugin --plugin-name clayz-presentation-skills-personal`，该包不得再交给 ChatGPT Skills 上传器。

演示文稿任务开始时，Supervisor 会盘点已挂载运行时、任务输入、所有者 Library、公共 Index、品牌资产、主机能力和字体，并在 Logic 前向用户说明发现与选用情况。所有者学习来源清单根据该次盘点在任务目录生成，再交给 `scripts/materialize_owner_index.py`；该清单及原始字节不会进入公开仓库。

## 上传和更新规则

1. 上传 composer 默认生成的单 Skill ZIP；不要把 marketplace 插件 ZIP 或五个分拆 Skill 交给 ChatGPT Skills 上传器；
2. 根目录必须只有一个 `SKILL.md`，`runtime/skill-mount-contract.json` 必须枚举并验证五个内部阶段模块；
3. 不要在 ChatGPT 中直接修改生成的 runtime 或 resolved config；应修改源 Profile 后重新生成；
4. 新增参考时，只更新 Library 附件、已准入 index record 和稳定位置上的 Provider manifest；Profile 或 Provider 清单不变时无需重新生成 cloud light；
5. 替换包后，用新会话做验收；
6. 旧五个自用 Skill 只在新单 Skill 验收期间作为回滚。直接调用、隐式调用、前置环境与资源简报、五阶段交接、必需资产失败关闭、PPTX 与完整审计报告成对交付、公共 fallback 全部通过后，再禁用或删除；
7. 过去用于维护 GitHub PPT 流程的 ChatGPT Project 不再是运行依赖，清点其独有文件后可以归档。

最终云端运行形态是“单一 ChatGPT Skill 发布入口 + 唯一 Cloud Public Light 脑 + 五个内部阶段模块 + ChatGPT 工具身体 + Personal Extension Profile + 私有 Library/索引记忆”。云端宿主的实际文件和工具能力可能与本地 Codex 不同；mount 只证明资料可发现，不代表某项工具或字体一定可用。Supervisor 必须先打开生命周期记录，保存规范化当前请求的原始字节，签发新鲜运行挑战及任务根签发记录，解析 `config/personal-extension-resolved.json`，再用同一任务字节在 Logic 前且只执行一次预检。预检绑定脚本签发的 run ID、任务哈希、nonce、task-root 摘要、规范签发/消费回执和配置实际哈希；复制或改名挑战不能重放，任务要求只能追加。“可用”的宿主能力必须绑定同一挑战并由经过哈希校验的 inventory 回执支持，但仍是 `host-declared-unverified`，只能形成 provisional/attemptable 路线，不能形成 ready。该路线可锁定尝试一次，只有最终 PPTX、对象与渲染被独立验证后才可交付。无法物化并在适用阶段实际选用全部必选私人 Provider，或既无 ready 也无 attemptable 制作/渲染路线时必须 fail closed。PowerPoint/WPS 等目标应用无论有无都要扫描，但其原生重开能力属于输出后验收观察，不属于开工硬条件；缺失时在最终报告中记录 `deferred` 并限制兼容性声明。最终交付必须由 `scripts/publish_supervised_pair.py` 物化，同时包含 PPTX 与 `ppt-supervision-report.json`，并由 `delivery-manifest.json` 证明二者成对；缺一不得标记完成。

每个任务开始时，按下面两步建立新鲜绑定。签发阶段还会生成 `.clayz-run-challenges/<run>.issued.json`，扫描阶段通过 `.clayz-run-challenges/consumed/<challenge-sha>.json` 唯一消费。扫描必须再次传入签发时的同一份不可变任务请求；挑战被复制/复用、缺少签发记录、任务根变化或任务字节变化都要 fail closed。若宿主声明演示工具可用，attestation 必须复述 challenge 字段，并通过 SHA-256 回执指向任务级 `host-tool-inventory/1.0` JSON；形成的路线仍为 provisional，直至最终产物验证通过。不要把瞬时能力清单写进 Profile 或 Library 索引。

```bash
python scripts/runtime_preflight.py --issue-challenge \
  --task-request <canonical-task-request.txt> --output <run-challenge.json>
python scripts/runtime_preflight.py --challenge <run-challenge.json> \
  --task-request <canonical-task-request.txt> \
  --host-capabilities <host-capability-attestation.json> \
  --output <runtime-preflight.json>
```
