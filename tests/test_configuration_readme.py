import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from configuration import load, ConfigurationError
from check_readme import check as check_readme


class ConfigAndReadmeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='public-skill-test-')
        self.root = Path(self.temp.name).resolve()
        self.addCleanup(self.temp.cleanup)
        self.config = self.root / 'config.local.json'
        self.data = {'schema_version': 1, 'github_account': 'alice-example', 'target_owner': 'example-org',
                     'integration_branch': 'develop', 'bugfix_strategy': 'branch', 'commit_language': 'en',
                     'rules_source': None, 'rules_sha256': None}

    def write(self):
        self.config.write_text(json.dumps(self.data), encoding='utf-8')

    def test_no_implicit_maintainer_account(self):
        with self.assertRaises(ConfigurationError):
            load(self.config)
        self.data['github_account'] = ''
        self.write()
        with self.assertRaises(ConfigurationError):
            load(self.config)

    def test_distinct_user_and_org(self):
        self.write()
        actual = load(self.config)
        self.assertEqual(actual['github_account'], 'alice-example')
        self.assertEqual(actual['target_owner'], 'example-org')

    def test_relative_rules_path_and_integration_preference(self):
        self.data.update(rules_source='my-rules.md', bugfix_strategy='integration')
        self.write()
        actual = load(self.config)
        self.assertEqual(actual['rules_source'], str(self.root / 'my-rules.md'))
        self.assertEqual(actual['bugfix_strategy'], 'integration')

    def test_bad_configuration_values(self):
        for field, value in [('target_owner', 'https://example.com'), ('bugfix_strategy', 'force'),
                             ('integration_branch', '--delete'), ('integration_branch', 'a//b'),
                             ('schema_version', True), ('rules_sha256', 'unverified')]:
            before = dict(self.data)
            self.data[field] = value
            self.write()
            with self.subTest(field=field), self.assertRaises(ConfigurationError):
                load(self.config)
            self.data = before

    def test_readme_github_layout_and_local_link(self):
        (self.root / 'SKILL.md').write_text('entry', encoding='utf-8')
        (self.root / 'README.md').write_text('<div align="center">\n\n# Example\n\n</div>\n\n[Skill](SKILL.md)\n<details><summary>Install</summary>\n\nText\n</details>', encoding='utf-8')
        self.assertEqual(check_readme(self.root), [])

    def test_readme_rejects_broken_link_css_and_unfilled_template(self):
        (self.root / 'README.md').write_text('{{PROJECT_NAME}}\n[Broken](missing.md)\n<div style="color:red">x</div>', encoding='utf-8')
        errors = check_readme(self.root)
        self.assertIn('unfilled_template', errors)
        self.assertIn('missing_or_outside_local_link', errors)
        self.assertIn('unsupported_or_active_html', errors)

    def test_readme_does_not_claim_nonexistent_license(self):
        (self.root / 'README.md').write_text('![License](https://img.shields.io/badge/license-MIT-green)', encoding='utf-8')
        self.assertIn('license_badge_without_matching_license', check_readme(self.root))


if __name__ == '__main__':
    unittest.main()
