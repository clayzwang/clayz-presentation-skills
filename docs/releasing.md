# Release management

`VERSION` is the only release-version source of truth. Plugin metadata, central configuration, PPTX custom properties, citation metadata, README badges, the Experience Center current-release marker, and the dated Changelog section must match it.

`config/component-versions.json` is the per-release core-component table used by the startup freshness gate. `prepare_release.py` updates its release-level version surfaces together with `VERSION`; contract component versions change only when their contracts actually change. Do not hand-edit the table in a built package.

## Prepare a release

Normal presentation work uses the installed-package offline check. Developers
who need official-latest or candidate-expiration enforcement must explicitly run
`python scripts/component_version_guard.py --mode release-check --output <report.json>`
(plus the candidate manifest when applicable). Never make this publishing check
a prerequisite for an already installed Skill to produce a presentation.

1. Keep completed changes under `## Unreleased` in `CHANGELOG.md`.
2. Run `python scripts/prepare_release.py X.Y.Z --date YYYY-MM-DD`.
3. Review the diff and run `python scripts/validate_all.py`.
4. Fetch the reviewed Windows CPython 3.12 wheels with `python scripts/fetch_offline_wheels.py --platform windows`, then build Cloud Public Light, Local Public Light, the Windows offline add-on, and `SHA256SUMS.txt` with `python scripts/build_runtime_packs.py --platform windows`.
5. Inspect every generated archive and confirm the archive audit passes. See [`release-packages.md`](release-packages.md).
6. If you maintain a separately composed Personal candidate, you may run `python scripts/validate_chatgpt_release_acceptance.py` against its evidence. This is an optional check for that candidate and is not a prerequisite for the public GitHub Release.
7. Submit and merge the version PR. Do not edit or create the Git tag manually.
8. A push to `main` that changes `VERSION` starts the deployed release workflow. You can also start the same workflow with `workflow_dispatch`. It validates the tree, resolves the version and bilingual notes, checks the immutable tag rule, builds and verifies the archives, and creates or completes the GitHub Release.

The preparation command updates only current-version surfaces. Historical Changelog headings, old Experience Center case profiles, versioned artifact filenames, and version-specific security reviews remain unchanged.

The deployed release workflow runs on the `VERSION` push path described above or by manual dispatch. Before publishing, it runs the repository validation suite and, when the external `CLAYZ_RELEASE_DENYLIST_B64` secret is configured, materializes that repository-external denylist for the release-hygiene scan. It builds exactly the declared archives and checksum file, refuses to move an existing tag away from the workflow commit, and leaves assets already attached to an existing release unchanged. A ChatGPT candidate receipt is not a deployed workflow prerequisite; the general acceptance validator remains available as an optional check.

## 中文说明

`VERSION` 是唯一发布版本真值。准备新版本时，先把已完成事项写入 `CHANGELOG.md` 的 `Unreleased`，再运行：

```bash
python scripts/prepare_release.py X.Y.Z --date YYYY-MM-DD
python scripts/validate_all.py
python scripts/fetch_offline_wheels.py --platform windows
python scripts/build_runtime_packs.py --platform windows
python scripts/verify_release_bundles.py --platform windows
```

脚本只更新“当前版本”位置，不会全局替换历史版本、旧体验案例文件名或版本特定的安全审查记录。v0.16.0 发版产物由 Cloud Public Light、Local Public Light、Windows CPython 3.12 离线依赖包和 SHA-256 清单组成；本版不生成其他操作系统包。细节见[`release-packages.zh-CN.md`](release-packages.zh-CN.md)。如果维护了单独组合的 ChatGPT Personal 候选包，可以使用 `python scripts/validate_chatgpt_release_acceptance.py` 校验其证据；这是可选检查，不是公共 GitHub Release 的前置条件。合并版本 PR 后，修改 `VERSION` 的 `main` 推送会自动启动已部署的 Release workflow，也可以使用 `workflow_dispatch` 手工启动。workflow 会执行完整仓库校验、版本与双语说明解析、不可变 Tag 检查、构建与归档校验，再创建或补全 GitHub Release。目标 Tag 如果已经指向其他提交，发布会直接失败，禁止覆盖旧版本。
