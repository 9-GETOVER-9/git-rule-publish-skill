"""Scan only the explicit public package inventory; report categories, not secrets."""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def findings(data, forbidden=()):
    text = data.decode('utf-8', errors='replace')
    found = []
    patterns = {
        'absolute_drive_path': r'\b[A-Za-z]:[\\/]',
        'unix_user_home': r'/(?:home|Users)/[A-Za-z0-9_.-]+/',
        'credential_pattern': r'gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}',
        'private_key': r'-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----',
    }
    for category, expression in patterns.items():
        if re.search(expression, text):
            found.append(category)
    if any(value.casefold() in text.casefold() for value in forbidden if value):
        found.append('explicit_forbidden_text')
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--forbid-text', action='append', default=[])
    args = parser.parse_args()
    meta = json.loads((ROOT / 'version.json').read_text(encoding='utf-8'))
    problems = []
    for name in meta['files']:
        if name.endswith('.local.json') or name in ('.env',):
            problems.append({'file': name, 'category': 'local_config_in_package'})
        for category in findings((ROOT / name).read_bytes(), args.forbid_text):
            problems.append({'file': name, 'category': category})
    print(json.dumps({'ok': not problems, 'findings': problems}))
    return 1 if problems else 0


if __name__ == '__main__':
    raise SystemExit(main())
