"""Verify and materialize the exact user-authorized frozen component package."""
import argparse
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    spec = json.loads((root / 'publication.json').read_text())
    archive = root / spec['archive']['name']
    raw = archive.read_bytes()
    assert len(raw) == spec['archive']['bytes']
    assert digest(raw) == spec['archive']['sha256']
    expected = {x['path']: x for x in spec['files']}
    destination = root / 'source'
    destination.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        assert len(bundle.infolist()) == len(expected)
        assert {x.filename for x in bundle.infolist()} == set(expected)
        for info in bundle.infolist():
            path = PurePosixPath(info.filename)
            assert not path.is_absolute() and '..' not in path.parts
            assert not info.is_dir() and not stat.S_ISLNK(info.external_attr >> 16)
            data = bundle.read(info)
            row = expected[info.filename]
            assert len(data) == row['bytes'] and digest(data) == row['sha256']
            target = destination.joinpath(*path.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                assert target.read_bytes() == data, 'Existing source differs from frozen bytes'
            else:
                target.write_bytes(data)
            if target.suffix == '.py':
                ast.parse(data, filename=info.filename)
    if spec['kind'] == 'knowledge':
        manifest = json.loads((destination / 'manifest.json').read_text())
        assert manifest['version'] == spec['version']
        for relative, sha in manifest['files'].items():
            assert digest((destination / relative).read_bytes()) == sha
    else:
        assert (destination / 'VERSION').read_text().strip() == spec['version']
    (root / 'SHA256SUMS.txt').write_text(spec['archive']['sha256'] + '  ' + archive.name + '\n')
    print(json.dumps({'status': 'verified', 'kind': spec['kind'], 'version': spec['version'],
                      'files': len(expected), 'archive_sha256': digest(raw),
                      'scope': 'Exact bytes, paths, CRC, Python syntax and package manifest. Not professional quality or target-application acceptance.'}))


if __name__ == '__main__':
    main()
