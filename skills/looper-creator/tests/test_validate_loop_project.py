import shutil
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from create_loop_project import create_project  # noqa: E402
from validate_loop_project import load_manifest, validate_manifest, validate_project  # noqa: E402


class LooperCreatorValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp(prefix="looper-creator-test-"))

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_valid_manifest_and_generated_project(self):
        manifest = load_manifest(SKILL_DIR / "examples" / "minimal-valid.loop.json")
        self.assertEqual([], validate_manifest(manifest))
        output = self.tmpdir / "generated"
        create_project(manifest, output)
        self.assertEqual([], validate_project(output))
        self.assertTrue((output / "scripts" / "verify.sh").exists())

    def test_invalid_manifest_is_rejected(self):
        manifest = load_manifest(SKILL_DIR / "examples" / "invalid-vague-goal.loop.json")
        errors = validate_manifest(manifest)
        self.assertTrue(errors)
        self.assertTrue(any("success_condition requires" in error for error in errors))
        self.assertTrue(any("verifier.command must not contain" in error for error in errors))

    def test_plaintext_secret_key_is_rejected(self):
        manifest = load_manifest(SKILL_DIR / "examples" / "minimal-valid.loop.json")
        manifest["verifier"]["token"] = "not-allowed"
        errors = validate_manifest(manifest)
        self.assertTrue(any("plaintext secret" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
