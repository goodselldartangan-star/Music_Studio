"""Q4 SFZ closure: source includes, true MIDI/pedal key release mapping."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.audit_salamander_full_q4 import (
    audit,resolve_source_refs,original_blob_sha,COUNTS)


def fixture(root:Path):
    (root/"Data").mkdir(parents=True,exist_ok=True)
    (root/"Salamander Grand Piano V3.sfz").write_text(
        "\n".join(f'#include "Data/{a}.txt"' for a in
                  ("notes","tune_nat","tune_ret","hammer","str_res","pedal")))
    (root/"Data/notes.txt").write_text('#include "Data/region.txt"\n')
    (root/"Data/region.txt").write_text(
        "\n".join(f"<region> sample=n{i}$VEL.$EXT" for i in range(30)))
    for suffix in ("nat","ret"):
        (root/f"Data/tune_{suffix}.txt").write_text("#define $TUNE01 0\n")
    for v in range(1,17):
        (root/f"Data/vel_{v:02d}.txt").write_text(f"#define $VEL v{v}\n")
    (root/"Data/hammer.txt").write_text(
        "\n".join(f"<region> key={k+20} sample=rel{k}.$EXT"
                  for k in range(1,89)))
    (root/"Data/str_res.txt").write_text(
        "\n".join(f"<region> sample=harm{g}{k}.$EXT"
                  for g in ("L","S","V3") for k in range(1,24)))
    (root/"Data/pedal.txt").write_text(
        "\n".join(f"<region> sample=pedal{state}{v}.$EXT"
                  for state in ("D","U") for v in (1,2)))
    groups=resolve_source_refs(root)
    tree={"truncated":False,"tree":[
        {"path":"Samples/"+name,"size":256,"type":"blob",
         "sha":"a"*40}
        for names in groups.values() for name in names]}
    tree_file=root/"full-tree.json"
    tree_file.write_text(json.dumps(tree))
    return groups,tree_file


class OriginalSalamanderAuditTests(unittest.TestCase):
    def test_all_source_regions_close_on_exact_original_tree(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            groups,tree=fixture(root)
            result=audit(root,tree)
            self.assertEqual(result["source_regions_by_group"],COUNTS)
            self.assertEqual(result["total_unique_original_flacs"],641)
            self.assertEqual(result["midi60_release_sample"],"rel40.flac")
            self.assertEqual(result["blob_sha_verified_count"],0)
            self.assertEqual(result["git_tree_total_bytes"],641*256)

    def test_missing_or_unreferenced_flac_cannot_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            _,tree=fixture(root)
            data=json.loads(tree.read_text())
            data["tree"].pop()
            tree.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,"SFZ/Git source mismatch"):
                audit(root,tree)
            data["tree"].append({"path":"Samples/unlisted.flac",
                                  "type":"blob","sha":"b"*40,"size":99})
            tree.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,"SFZ/Git source mismatch"):
                audit(root,tree)

    def test_wrong_midi60_release_mapping_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            _,tree=fixture(root)
            hammer=root/"Data/hammer.txt"
            hammer.write_text(hammer.read_text().replace(
                "key=60 sample=rel40.$EXT","key=60 sample=rel60.$EXT"))
            with self.assertRaisesRegex(ValueError,"MIDI-60"):
                audit(root,tree)

    def test_any_wrong_midi_key_release_sample_is_caught(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            _,tree=fixture(root)
            hammer=root/"Data/hammer.txt"
            hammer.write_text(hammer.read_text().replace(
                "key=61 sample=rel41.$EXT","key=61 sample=rel42.$EXT"))
            with self.assertRaisesRegex(ValueError,"MIDI 21-108"):
                audit(root,tree)

    def test_no_sample_bytes_can_be_claimed_verified_without_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            _,tree=fixture(root)
            with self.assertRaises(FileNotFoundError):
                audit(root,tree,verify_sample_bytes=True)

    def test_original_git_blob_hash_uses_length_prefix(self):
        with tempfile.TemporaryDirectory() as temp:
            test=Path(temp)/"sample.bin"
            raw=b"this is test audio bytes"
            test.write_bytes(raw)
            h=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\x00"+raw).hexdigest()
            self.assertEqual(original_blob_sha(test),h)


if __name__=="__main__":
    unittest.main()
