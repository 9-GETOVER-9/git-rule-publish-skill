"""Validate bundled rules and explicitly configured external rules without printing text."""
import argparse
import hashlib
import json
from pathlib import Path
from configuration import load, ConfigurationError, ROOT


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(config, metadata, root=ROOT):
    actual = digest(root / metadata['copy'])
    if actual != metadata['sha256']:
        return {'status': 'bundled_rules_changed', 'ok': False}
    source = config.get('rules_source')
    if source is None:
        return {'status': 'bundled_verified', 'ok': True, 'sha256': actual}
    try:
        actual = digest(Path(source))
    except OSError:
        return {'status': 'external_source_unavailable', 'ok': False}
    if not config.get('rules_sha256'):
        return {'status': 'external_unpinned_review_required', 'ok': False, 'sha256': actual}
    return {'status': 'external_verified' if actual == config['rules_sha256'].lower() else 'external_drift',
            'ok': actual == config['rules_sha256'].lower(), 'sha256': actual}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path)
    args = parser.parse_args()
    try:
        config = load(args.config)
        metadata = json.loads((ROOT / 'version.json').read_text(encoding='utf-8'))['rules']
        result = check(config, metadata)
    except (ConfigurationError, OSError, ValueError, KeyError):
        result = {'status': 'configuration_or_rules_invalid', 'ok': False}
    print(json.dumps(result))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
