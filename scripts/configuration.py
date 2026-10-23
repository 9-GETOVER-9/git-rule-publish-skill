"""Explicit local configuration. No identity is inferred from Git remotes."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


class ConfigurationError(Exception):
    pass


def load(path=None):
    path = Path(path) if path is not None else ROOT / 'config.local.json'
    try:
        data = json.loads(path.read_text(encoding='utf-8-sig'))
    except (OSError, ValueError):
        raise ConfigurationError('configuration_missing_or_invalid') from None
    if not isinstance(data, dict) or type(data.get('schema_version')) is not int or data['schema_version'] != 1:
        raise ConfigurationError('unsupported_configuration_schema')
    for field in ('github_account', 'target_owner'):
        if not isinstance(data.get(field), str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]*', data[field]):
            raise ConfigurationError('configure_account_and_target_owner')
    if data.get('bugfix_strategy') not in ('branch', 'integration'):
        raise ConfigurationError('invalid_bugfix_strategy')
    branch = data.get('integration_branch')
    if not isinstance(branch, str) or not re.fullmatch(r'[A-Za-z0-9\u4e00-\u9fff][A-Za-z0-9\u4e00-\u9fff._/-]*', branch) or '..' in branch or '@{' in branch or branch.endswith(('/', '.', '.lock')) or any(not part or part.startswith('.') or part.endswith('.lock') for part in branch.split('/')):
        raise ConfigurationError('invalid_integration_branch')
    if data.get('commit_language') not in ('zh-CN', 'en'):
        raise ConfigurationError('unsupported_commit_language')
    source = data.get('rules_source')
    digest = data.get('rules_sha256')
    if source is not None and (not isinstance(source, str) or not source.strip()):
        raise ConfigurationError('invalid_rules_source')
    if digest is not None and (not isinstance(digest, str) or not re.fullmatch(r'[a-fA-F0-9]{64}', digest)):
        raise ConfigurationError('invalid_rules_digest')
    if source is not None:
        resolved = Path(source).expanduser()
        data['rules_source'] = str((path.resolve().parent / resolved).resolve())
    return data
