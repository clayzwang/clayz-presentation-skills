# 发版包说明

v0.5.2 从唯一公共核心构建两个公共 Light 目标，继续把本地第三方 Python 依赖分开发布，并在公共发版路径之外增加所有者私有的云端 composer。本地发版以 Windows 为首发验证环境，本版不发布其他操作系统包。

## 文件组成

- `clayz-presentation-skills-0.5.2-cloud-light.zip` 是面向 ChatGPT 的公共脑；它使用宿主工具，不包含本地适配器、系统包或离线依赖。
- `clayz-presentation-skills-0.5.2-local-light.zip` 是通过 Windows 验证的本地公共插件；可以联网运行`python -m pip install -r requirements.txt`，也可以搭配下面的 Windows 离线包。
- `clayz-presentation-skills-0.5.2-offline-windows-py312.zip`适用于Windows x86-64与CPython 3.12。
- `SHA256SUMS.txt`记录两个 Light 与 Windows 离线附加包的校验值。

v0.5.2 不生成 macOS、Linux 或 iOS 压缩包。源码层的可移植接口属于后续工作，不能视为已经测试的发布承诺。

离线包只是 Local Public Light 的依赖附加包，不能代替插件主包，也绝不是 Cloud Light 的依赖。解压后运行：

```bash
python install_offline_dependencies.py
```

安装器固定使用`--no-index`、`--only-binary`和`--require-hashes`，不会访问软件源；需要隔离安装时可增加`--target <目录>`。本地环境能够正常联网安装`requirements.txt`时，只下载 Local Public Light 即可。

## 内容边界

两个公共 Light 都包含相同的 `public_core_sha256`、随包公共 Provider manifest/index 与五阶段方法，并排除体验中心案例、示例、测试、PPT/PDF、展示媒体、字体、缓存、私有 Profile、私有 Provider manifest、私有索引和发版工作文件。Cloud Light 还排除本地执行适配器与系统包。Windows 离线包只包含经过审阅的依赖 wheel、精确哈希锁、离线安装器、机器可读清单及第三方许可说明。PowerPoint、WPS、Poppler 和 Python 本身都不随这些压缩包分发。

`scripts/compose_personal_light.py` 是独立的本地私有流程。它只读取仓库外的私有输入，并把私有云端 ZIP 写入 `dist/private/`；该 ZIP 不是公共 release artifact。详见[`chatgpt-personal-light.zh-CN.md`](chatgpt-personal-light.zh-CN.md)。

每个 ZIP 生成后都会重新打开并扫描。如果成员路径、可读文本、嵌套 wheel 路径或 wheel 中的许可/元数据命中仓库外 `CLAYZ_RELEASE_DENYLIST`，构建立即失败并删除候选压缩包。denylist 本身永不提交、也不进入发布包。

## 维护者命令

```bash
python scripts/validate_all.py
python scripts/fetch_offline_wheels.py --platform windows
python scripts/build_runtime_packs.py --platform windows
python scripts/verify_release_bundles.py --platform windows
```

`.release-cache/`只是本地wheel暂存目录，不得发布；官方wheel的内容和许可元数据必须原样保留。
