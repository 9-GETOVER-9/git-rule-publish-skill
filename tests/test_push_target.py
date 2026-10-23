import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from check_push_target import check as real_check, main, parse_https, TargetError

def check(repo, expected):
    return real_check(repo, expected, Path(repo) / 'config.local.json')
from check_rules import check as check_rules, digest

URL = 'https://github.com/example-user/example.git'
EXPECTED = 'example-user/example'


class PushTargetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='skill-push-test-')
        self.root = Path(self.temp.name).resolve()
        # Each cleanup is limited to the absolute TemporaryDirectory created here.
        self.addCleanup(self.temp.cleanup)
        env = dict(os.environ)
        for key in list(env):
            if key.startswith('GIT_'):
                del env[key]
        env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT='0')
        self.patch_env = patch.dict(os.environ, env, clear=True)
        self.patch_env.start()
        self.addCleanup(self.patch_env.stop)
        self.git('init', '--quiet')
        self.git('remote', 'add', 'origin', URL)
        config = {'schema_version': 1, 'github_account': 'example-user', 'target_owner': 'example-user',
                  'integration_branch': 'dev', 'bugfix_strategy': 'branch', 'commit_language': 'zh-CN',
                  'rules_source': None, 'rules_sha256': None}
        (self.root / 'config.local.json').write_text(json.dumps(config), encoding='utf-8')

    def git(self, *args):
        subprocess.run(['git', '-C', str(self.root), *args], check=True, capture_output=True)

    def test_allowed_https(self):
        result = check(self.root, EXPECTED)
        self.assertTrue(result['ok'])
        self.assertFalse(result['identity_verified'])

    def test_configured_organization_with_separate_login(self):
        path = self.root / 'config.local.json'
        config = json.loads(path.read_text(encoding='utf-8'))
        config['target_owner'] = 'example-org'
        path.write_text(json.dumps(config), encoding='utf-8')
        self.git('remote', 'set-url', 'origin', 'https://github.com/example-org/tool.git')
        self.assertTrue(check(self.root, 'example-org/tool')['ok'])
        with self.assertRaises(TargetError):
            check(self.root, EXPECTED)

    def test_hidden_pushurl_wrong_owner(self):
        self.git('config', 'remote.origin.pushurl', 'https://github.com/somebody/example.git')
        with self.assertRaises(TargetError):
            check(self.root, EXPECTED)

    def test_same_owner_wrong_repository(self):
        self.git('config', 'remote.origin.pushurl', 'https://github.com/example-user/unrelated.git')
        with self.assertRaises(TargetError):
            check(self.root, EXPECTED)

    def test_every_pushurl_is_checked(self):
        self.git('config', '--add', 'remote.origin.pushurl', URL)
        self.git('config', '--add', 'remote.origin.pushurl', 'https://example.org/example-user/example.git')
        with self.assertRaises(TargetError):
            check(self.root, EXPECTED)

    def test_pushinstead_of_rewrite(self):
        self.git('config', 'url.https://evil.invalid/.pushInsteadOf', 'https://github.com/')
        with self.assertRaises(TargetError):
            check(self.root, EXPECTED)

    def test_instead_of_rewrite(self):
        self.git('config', 'url.https://evil.invalid/.insteadOf', 'https://github.com/')
        with self.assertRaises(TargetError):
            check(self.root, EXPECTED)

    def test_explicit_pushurl_ignores_pushinstead_of_as_git_does(self):
        self.git('config', 'remote.origin.pushurl', URL)
        self.git('config', 'url.https://evil.invalid/.pushInsteadOf', 'https://github.com/')
        self.assertTrue(check(self.root, EXPECTED)['ok'])

    def test_ssh_alias_and_direct_ssh_require_review(self):
        for url in ('git@github.com:example-user/example.git', 'ssh://git@myalias/example-user/example.git'):
            self.git('config', 'remote.origin.pushurl', url)
            with self.subTest(url=url), self.assertRaises(TargetError):
                check(self.root, EXPECTED)

    def test_sensitive_urls_and_host_confusion(self):
        for url in ('https://token123@github.com/example-user/example',
                    URL + '?token=secret', URL + '#secret',
                    'https://github.com.evil/example-user/example',
                    'https://github.com:123/example-user/example',
                    'https://github.com/example-user/%65xample',
                    'file:///tmp/repo', 'ext::echo secret',
                    'https://github.com/example-user/example\n'):
            with self.subTest(url=url), self.assertRaises(TargetError):
                parse_https(url)

    def test_error_does_not_print_credentials(self):
        self.git('config', 'remote.origin.pushurl', 'https://very-secret-token@github.com/example-user/example')
        capture = io.StringIO()
        with patch.object(sys, 'argv', ['guard', '--repo', str(self.root), '--expected-repo', EXPECTED, '--config', str(self.root / 'config.local.json')]), contextlib.redirect_stdout(capture):
            self.assertEqual(main(), 1)
        self.assertNotIn('very-secret-token', capture.getvalue())
        self.assertFalse(json.loads(capture.getvalue())['ok'])

    def test_missing_origin(self):
        self.git('remote', 'remove', 'origin')
        with self.assertRaises(TargetError):
            check(self.root, EXPECTED)

    def test_invalid_expected_owner(self):
        with self.assertRaises(TargetError):
            check(self.root, 'somebody/example')

    def test_does_not_modify_repository_configuration(self):
        config = self.root / '.git/config'
        before = config.read_bytes()
        check(self.root, EXPECTED)
        self.assertEqual(before, config.read_bytes())

    def test_rule_source_drift_and_missing(self):
        source, copy = self.root / 'source.md', self.root / 'copy.md'
        source.write_text('Custom rules', encoding='utf-8')
        copy.write_text('Bundled defaults', encoding='utf-8')
        meta = {'copy': 'copy.md', 'sha256': digest(copy)}
        cfg = {'rules_source': None}
        self.assertEqual(check_rules(cfg, meta, self.root)['status'], 'bundled_verified')
        cfg = {'rules_source': str(source), 'rules_sha256': None}
        self.assertFalse(check_rules(cfg, meta, self.root)['ok'])
        cfg['rules_sha256'] = digest(source)
        self.assertEqual(check_rules(cfg, meta, self.root)['status'], 'external_verified')
        source.write_text('Changed', encoding='utf-8')
        self.assertFalse(check_rules(cfg, meta, self.root)['ok'])
        cfg['rules_source'] = str(self.root / 'missing')
        self.assertEqual(check_rules(cfg, meta, self.root)['status'], 'external_source_unavailable')


if __name__ == '__main__':
    unittest.main()
