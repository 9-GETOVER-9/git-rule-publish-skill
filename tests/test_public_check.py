from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from public_check import findings


class PublicCheckTests(unittest.TestCase):
    def test_private_path_and_credentials_are_found_without_echo(self):
        fake_path = 'Z' + ':' + '/' + 'Users/demo/private'
        fake_key = 'ghp_' + 'a' * 36
        output = findings((fake_path + ' ' + fake_key).encode())
        self.assertIn('absolute_drive_path', output)
        self.assertIn('credential_pattern', output)
        self.assertNotIn(fake_key, str(output))

    def test_portable_examples_and_public_links_are_allowed(self):
        self.assertEqual(findings(b'~/.codex/skills https://github.com/example/repo'), [])

    def test_operator_specified_sensitive_text(self):
        self.assertEqual(findings(b'private-label', ['PRIVATE-LABEL']), ['explicit_forbidden_text'])


if __name__ == '__main__':
    unittest.main()
