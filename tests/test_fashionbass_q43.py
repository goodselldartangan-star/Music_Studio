"""Q4.3 pinned full CC0 bass source closure, no fake release events."""
import json
import tempfile
import unittest
from pathlib import Path

from tools.probe_fashionbass_q43 import validate_source,refs,prepare_minimal_original,SOURCES


class FashionbassTests(unittest.TestCase):
    def test_two_original_wav_names_explicitly_pinned(self):
        self.assertEqual(len(SOURCES),2)
        self.assertTrue(all(len(x)==40 for x in SOURCES.values()))

    def test_unsafe_paths_and_duplicate_sfzs_fail(self):
        with self.assertRaises(ValueError):
            refs("<region> sample=../evil.wav")
        with self.assertRaises(ValueError):
            refs("<region> sample=notes/one.wav\n<region> sample=notes/one.wav")

    def test_complete_guitar_styled_source_manifest_fail_closed(self):
        manifest={"pinned_commit":"wrong","truncated":False,"samples":[]}
        with self.assertRaisesRegex(ValueError,"revision"):
            validate_source("", "",manifest)
        manifest["pinned_commit"]="0703973b300a6bacb837602be9b588ab64732a72"
        with self.assertRaisesRegex(ValueError,"manifest"):
            validate_source("", "",manifest)

    def test_minimal_release_probe_does_not_synthesize_fake_audio(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with self.assertRaises(FileNotFoundError):
                prepare_minimal_original(root)
            for name in SOURCES:
                p=root/"Samples"/name
                p.parent.mkdir(parents=True,exist_ok=True)
                p.write_bytes(b"fixture data (not source audio)")
            prepare_minimal_original(root)
            base=(root/"Q43_note_only.sfz").read_text()
            with_rel=(root/"Q43_original_release.sfz").read_text()
            self.assertIn("notes/d2_mf_rr1.wav",base)
            self.assertNotIn("trigger=release",base)
            self.assertTrue(with_rel.startswith(base))
            self.assertEqual(with_rel.count("trigger=release"),1)
            self.assertIn("release/d2_release_rr1.wav",with_rel)
            self.assertTrue((root/"Q43_original_release.mid").is_file())
            for name in SOURCES:
                self.assertEqual((root/"Samples"/name).read_bytes(),
                                 b"fixture data (not source audio)")


if __name__=="__main__":
    unittest.main()
