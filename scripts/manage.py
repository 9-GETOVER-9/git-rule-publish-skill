"""Validate or deterministically package this installed skill. Never uploads."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import posixpath
import zipfile

import yaml

ROOT = Path(__file__).resolve().parents[1]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def safe_name(name):
    if not isinstance(name, str) or '\\' in name or ':' in name:
        raise ValueError('Invalid package path')
    path = PurePosixPath(name)
    if path.is_absolute() or any(p in ('', '.', '..') for p in name.split('/')):
        raise ValueError('Unsafe package path')
    return path


def local_file(root, name):
    path = root.joinpath(*safe_name(name).parts)
    if not path.resolve().is_relative_to(root.resolve()) or path.is_symlink():
        raise ValueError('Linked/outside files are not allowed')
    for parent in path.parents:
        if parent == root:
            break
        if parent.is_symlink():
            raise ValueError('Linked directories are not allowed')
    if not path.is_file():
        raise ValueError('Required package file is missing: ' + name)
    return path


def payload(root):
    meta = json.loads((root / 'version.json').read_text(encoding='utf-8'))
    names = meta['files']
    if not isinstance(names, list) or len(names) != len(set(names)) or 'manifest.json' in names:
        raise ValueError('Invalid file inventory')
    if not {'version.json', 'SKILL.md', 'agents/openai.yaml'}.issubset(names):
        raise ValueError('Incomplete skill inventory')
    data = {name: local_file(root, name).read_bytes() for name in sorted(names)}
    validate_contract(meta, data)
    return meta, data


def validate_contract(meta, data):
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', meta['name']):
        raise ValueError('Invalid skill name')
    if not re.fullmatch(r'\d+\.\d+\.\d+', meta['version']):
        raise ValueError('Invalid version')
    text = data['SKILL.md'].decode('utf-8-sig')
    match = re.match(r'\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)', text, re.S)
    if not match:
        raise ValueError('Missing frontmatter')
    header = yaml.safe_load(match.group(1))
    if header.get('name') != meta['name'] or not isinstance(header.get('description'), str) or not header['description'].strip():
        raise ValueError('Skill metadata mismatch')
    interface = yaml.safe_load(data['agents/openai.yaml'])['interface']
    if '$' + meta['name'] not in interface['default_prompt'] or not interface['display_name']:
        raise ValueError('Interface mismatch')
    # Simple relative file links used by these packages; absolute/HTTP links aren't bundled dependencies.
    for source, value in data.items():
        if not source.endswith('.md'):
            continue
        for target in re.findall(r'\]\(([^)]+)\)', value.decode('utf-8-sig')):
            if ':' in target or target.startswith(('#', '/')):
                continue
            name = posixpath.normpath((PurePosixPath(source).parent / target.split('#')[0]).as_posix())
            safe_name(name)
            if name not in data:
                raise ValueError('Unbundled reference: ' + name)


def manifest_for(meta, data):
    return {'name': meta['name'], 'version': meta['version'],
            'sha256': {name: sha(value) for name, value in sorted(data.items())}}


def check(root=ROOT):
    meta, data = payload(root)
    recorded = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    if recorded != manifest_for(meta, data):
        raise ValueError('Manifest mismatch: review edits, then explicitly refresh it')
    return meta, data


def build(destination, root=ROOT):
    meta, data = check(root)
    data['manifest.json'] = (root / 'manifest.json').read_bytes()
    # Exclusive create: a release or backup is never silently replaced.
    with zipfile.ZipFile(destination, 'x', compression=zipfile.ZIP_STORED) as archive:
        for name, value in sorted(data.items()):
            entry = zipfile.ZipInfo(meta['name'] + '/' + name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, value)
    return sha(Path(destination).read_bytes())


def verify_zip(path, root=ROOT):
    meta, expected = check(root)
    expected['manifest.json'] = (root / 'manifest.json').read_bytes()
    prefix = meta['name'] + '/'
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or set(names) != {prefix + n for n in expected}:
            raise ValueError('Archive inventory mismatch')
        for name in names:
            safe_name(name)
            wanted = expected[name[len(prefix):]]
            # Bound memory by the known, locally verified payload size.
            if archive.getinfo(name).file_size != len(wanted) or archive.read(name) != wanted:
                raise ValueError('Archive content mismatch')
    return sha(Path(path).read_bytes())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['check', 'refresh-manifest', 'build', 'verify-zip'])
    parser.add_argument('--output', type=Path)
    parser.add_argument('--archive', type=Path)
    args = parser.parse_args()
    try:
        if args.action == 'refresh-manifest':
            meta, data = payload(ROOT)
            (ROOT / 'manifest.json').write_text(json.dumps(manifest_for(meta, data), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            result = 'Manifest updated after explicit maintenance request'
        elif args.action == 'check':
            meta, _ = check()
            result = meta['name'] + ' ' + meta['version'] + ': package check passed'
        elif args.action == 'build':
            if not args.output:
                parser.error('--output is required')
            result = build(args.output)
        else:
            if not args.archive:
                parser.error('--archive is required')
            result = verify_zip(args.archive)
        print(result)
        return 0
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError, zipfile.BadZipFile):
        print('Check failed; inspect package structure or manifest locally. No files uploaded.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
