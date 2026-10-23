import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import manage


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='skill-package-test-')
        self.root = Path(self.temp.name).resolve()
        self.addCleanup(self.temp.cleanup)
        self.skill = self.root / 'skill'
        self.skill.mkdir()
        meta = json.loads((manage.ROOT / 'version.json').read_text(encoding='utf-8'))
        for name in meta['files'] + ['manifest.json']:
            target = self.skill / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(manage.ROOT / name, target)

    def test_installed_package_is_valid(self):
        meta, data = manage.check(self.skill)
        self.assertTrue(data['SKILL.md'])

    def test_edit_without_manifest_refresh_fails(self):
        with (self.skill / 'SKILL.md').open('a', encoding='utf-8') as stream:
            stream.write('\nChanged instruction\n')
        with self.assertRaises(ValueError):
            manage.check(self.skill)

    def test_missing_entry_fails(self):
        # Delete only the named file inside this test's checked temporary root.
        target = (self.skill / 'SKILL.md').resolve()
        self.assertTrue(target.is_relative_to(self.root))
        target.unlink()
        with self.assertRaises(ValueError):
            manage.check(self.skill)

    def test_deterministic_archive_and_roundtrip(self):
        one, two = self.root / 'one.zip', self.root / 'two.zip'
        self.assertEqual(manage.build(one, self.skill), manage.build(two, self.skill))
        self.assertEqual(manage.verify_zip(one, self.skill), hashlib.sha256(one.read_bytes()).hexdigest())

    def test_zip_with_extra_or_traversal_entry_is_rejected(self):
        archive = self.root / 'bad.zip'
        manage.build(archive, self.skill)
        with zipfile.ZipFile(archive, 'a') as z:
            z.writestr('../unexpected.txt', 'untrusted')
        with self.assertRaises(ValueError):
            manage.verify_zip(archive, self.skill)

    def test_package_does_not_overwrite_existing_output(self):
        archive = self.root / 'original.zip'
        archive.write_bytes(b'keep')
        with self.assertRaises(FileExistsError):
            manage.build(archive, self.skill)
        self.assertEqual(archive.read_bytes(), b'keep')

    def test_broken_relative_reference_is_detected(self):
        meta, data = manage.payload(self.skill)
        data['SKILL.md'] += b'\n[Missing](references/not-packaged.md)\n'
        with self.assertRaises(ValueError):
            manage.validate_contract(meta, data)

    def test_unsafe_inventory_paths_are_rejected(self):
        for path in ('../outside', '/absolute', 'C' + ':/secret', 'dir\\file', 'a//b'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                manage.safe_name(path)

    def test_unlisted_private_files_not_packaged(self):
        (self.skill / 'private-notes.txt').write_text('NOT-FOR-PACKAGE', encoding='utf-8')
        archive = self.root / 'safe.zip'
        manage.build(archive, self.skill)
        with zipfile.ZipFile(archive) as z:
            self.assertFalse(any('private-notes' in name for name in z.namelist()))


if __name__ == '__main__':
    unittest.main()
