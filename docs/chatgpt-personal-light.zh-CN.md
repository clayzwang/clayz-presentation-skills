# ChatGPT Personal Light

本文规定 `scripts/compose_personal_light.py` 生成的私有 ZIP 如何交给 ChatGPT。[OpenAI 官方 Skill 格式](https://learn.chatgpt.com/docs/build-skills)允许 instructions、references、assets、scripts 和 UI metadata，插件也可以包含多个 Skill。因此 composer 以 Cloud Public Light 为脑，保留既有五个阶段和随包公共 Provider，再接入一份生成的 runtime/config；ChatGPT 已有工具构成身体，不依赖同名 Skill 自动合并，也不重复打包本地执行环境。

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

默认输出写入 `dist/private/`；该目录不进入公共 release scan，也不应被 Git 跟踪。ZIP 以 Cloud Public Light 为基础，包含唯一 Public Core、公共 Provider manifest/index、五个 Skill、一份生成的 resolved config 和 `runtime/personal-extension.json`。它不包含本地适配器、系统包、源 Profile、源私有 manifest、私有 JSONL 索引、附件、母版、字体或案例。

## 上传和更新规则

1. 上传 composer 生成的 personal cloud composition ZIP；Cloud Public Light 是它的公共脑底座，不应与个人组合包重复安装；
2. 不要再安装一组同名私有 Skill，并期待 ChatGPT 自动合并；
3. 不要在 ChatGPT 中直接修改生成的 runtime 或 resolved config；应修改源 Profile 后重新生成；
4. 新增参考时，只更新 Library 附件、已准入 index record 和稳定位置上的 Provider manifest；Profile 或 Provider 清单不变时无需重新生成 cloud light；
5. 替换包后，用新会话做验收；
6. 旧五个自用 Skill 暂时作为回滚。直接调用、隐式调用、五阶段交接、必需资产失败关闭和公共 fallback 全部通过后，再禁用或归档；
7. 过去用于维护 GitHub PPT 流程的 ChatGPT Project 不再是运行依赖，清点其独有文件后可以归档。

最终云端运行形态是“Cloud Public Light 脑 + ChatGPT 工具身体 + Personal Extension Profile + 私有 Library/索引记忆”。云端宿主的实际文件和工具能力可能与本地 Codex 不同；mount 只证明资料可发现，不代表某项工具或字体一定可用。Output 仍必须执行宿主能力预检；无法物化必需私有资产时必须 fail closed。

每个任务开始时，宿主适配器应检查可用演示工具，并向 `scripts/runtime_preflight.py --host-capabilities <json>` 传入等价的任务级声明。不要把这份瞬时能力清单写进 Profile 或 Library 索引。
