"""Offline, read-only Git destination check. Never prints raw URLs or stderr."""
import argparse
import json
import re
import subprocess
from urllib.parse import urlsplit

from configuration import load, ConfigurationError


class TargetError(Exception):
    pass


def canonical_repo(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', value):
        raise TargetError('invalid_expected_repository')
    owner, repo = value.split('/')
    if repo in ('.', '..') or repo.lower().endswith('.git'):
        raise TargetError('expected_repository_not_allowed')
    return owner.lower() + '/' + repo.lower()


def parse_https(url):
    if not isinstance(url, str) or any(c.isspace() or ord(c) < 32 for c in url):
        raise TargetError('invalid_destination')
    if url.startswith(('ssh://', 'git@')) or re.match(r'^[^/]+@[^:]+:', url):
        raise TargetError('ssh_requires_manual_transport_and_identity_review')
    try:
        p = urlsplit(url)
        if p.scheme != 'https' or p.hostname != 'github.com' or p.port not in (None, 443):
            raise TargetError('unsupported_destination')
        if p.username is not None or p.password is not None or p.query or p.fragment or '?' in url or '#' in url:
            raise TargetError('credentials_or_url_parameters_not_allowed')
        path = p.path.removeprefix('/').removesuffix('/')
        if path.endswith('.git'):
            path = path[:-4]
        return canonical_repo(path)
    except ValueError:
        raise TargetError('invalid_destination') from None


def git_lines(repo, args):
    try:
        result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True,
                                text=True, encoding='utf-8', errors='replace', timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        raise TargetError('git_metadata_unavailable') from None
    if result.returncode:
        raise TargetError('git_metadata_failed')
    values = result.stdout.splitlines()
    if not values or any(not v for v in values):
        raise TargetError('missing_destination')
    return values


def check(repo, expected_repo, config_path=None):
    config = load(config_path)
    expected = canonical_repo(expected_repo)
    if expected.split('/')[0] != config['target_owner'].lower():
        raise TargetError('owner_not_allowed_by_selected_configuration')
    # Git expands insteadOf / pushInsteadOf here, including explicit pushurl.
    fetch = git_lines(repo, ['remote', 'get-url', '--all', 'origin'])
    push = git_lines(repo, ['remote', 'get-url', '--push', '--all', 'origin'])
    for value in fetch + push:
        if parse_https(value) != expected:
            raise TargetError('destination_does_not_match_authorized_repository')
    return {'ok': True, 'repository': expected, 'fetch_count': len(fetch),
            'push_count': len(push), 'network_used': False, 'identity_verified': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True)
    parser.add_argument('--expected-repo', required=True)
    parser.add_argument('--config')
    args = parser.parse_args()
    try:
        output = check(args.repo, args.expected_repo, args.config)
    except (TargetError, ConfigurationError) as exc:
        print(json.dumps({'ok': False, 'reason': str(exc), 'network_used': False}))
        return 1
    print(json.dumps(output))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
