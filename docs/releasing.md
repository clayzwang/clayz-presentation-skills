# Release management

`VERSION` is the only release-version source of truth. Plugin metadata, central configuration, PPTX custom properties, citation metadata, README badges, the Experience Center current-release marker, and the dated Changelog section must match it.

## Prepare a release

1. Keep completed changes under `## Unreleased` in `CHANGELOG.md`.
2. Run `python scripts/prepare_release.py X.Y.Z --date YYYY-MM-DD`.
3. Review the diff and run `python scripts/validate_all.py`.
4. Submit and merge the version PR. Do not edit or create the Git tag manually.
5. A merge that changes `VERSION` triggers the release workflow. The workflow validates the whole tree, creates the versioned archive and checksum, and creates the GitHub Release.

The preparation command updates only current-version surfaces. Historical Changelog headings, old Experience Center case profiles, versioned artifact filenames, and version-specific security reviews remain unchanged.

The release workflow is fail-closed: all current-version surfaces must agree, the Changelog must contain a dated section, and an existing tag may be reused only when it already points to the exact workflow commit. It never moves an old release tag.

## 中文说明

`VERSION` 是唯一发布版本真值。准备新版本时，先把已完成事项写入 `CHANGELOG.md` 的 `Unreleased`，再运行：

```bash
python scripts/prepare_release.py X.Y.Z --date YYYY-MM-DD
python scripts/validate_all.py
```

脚本只更新“当前版本”位置，不会全局替换历史版本、旧体验案例文件名或版本特定的安全审查记录。包含 `VERSION` 变化的PR合并后才会触发GitHub Release；若目标Tag已经指向其他提交，发布会直接失败，禁止覆盖旧版本。
