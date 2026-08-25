# 发版包说明

v0.5.1把插件代码与可选的第三方Python依赖分开发布。

## 文件组成

- `clayz-presentation-skills-0.5.1-light.zip`是默认轻量主包。可以联网运行`python -m pip install -r requirements.txt`，也可以搭配下面对应系统的离线包。
- `clayz-presentation-skills-0.5.1-offline-windows-py312.zip`适用于Windows x86-64与CPython 3.12。
- `clayz-presentation-skills-0.5.1-offline-macos-py312.zip`适用于macOS arm64/x86-64与CPython 3.12。
- `clayz-presentation-skills-0.5.1-offline-linux-py312.zip`适用于manylinux 2.28 x86-64/aarch64与CPython 3.12。
- `SHA256SUMS.txt`记录以上四个压缩包的校验值。

离线包只是依赖附加包，不能代替插件主包。解压与本机匹配的离线包后运行：

```bash
python install_offline_dependencies.py
```

安装器固定使用`--no-index`、`--only-binary`和`--require-hashes`，不会访问软件源；需要隔离安装时可增加`--target <目录>`。环境能够正常联网安装`requirements.txt`时，只下载轻量主包即可。

## 内容边界

轻量主包排除体验中心案例、示例、测试、PPT/PDF、展示媒体、字体、缓存和发版工作文件。离线包只包含经过审阅的依赖wheel、精确哈希锁、离线安装器、机器可读清单及第三方许可说明。PowerPoint、WPS、LibreOffice、Poppler和Python本身都不随这些压缩包分发。

每个ZIP生成后都会重新打开并扫描。如果成员路径、可读文本、嵌套wheel路径或wheel中的许可/元数据出现私有企业展示标识，构建立即失败并删除候选压缩包。

## 维护者命令

```bash
python scripts/validate_all.py
python scripts/fetch_offline_wheels.py
python scripts/build_runtime_packs.py
python scripts/verify_release_bundles.py
```

`.release-cache/`只是本地wheel暂存目录，不得发布；官方wheel的内容和许可元数据必须原样保留。
