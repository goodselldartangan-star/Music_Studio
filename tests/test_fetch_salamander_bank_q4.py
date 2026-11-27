"""Q4 full licensed bank downloader: pin integrity, no uncontrolled overwrites."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.fetch_salamander_bank_q4 import install_one


class SalamanderBankDownloaderTests(unittest.TestCase):
    def test_a_publisher_blob_is_written_once_and_reused_without_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            pcm=b"fake fixture, not copyrighted audio data"
            sha=hashlib.sha1(b"blob "+str(len(pcm)).encode()+b"\x00"+pcm).hexdigest()
            with patch("tools.fetch_salamander_bank_q4._read_url",return_value=pcm) as fetch:
                self.assertEqual(install_one(root,"C4v12.flac",sha,len(pcm)),"downloaded")
                self.assertEqual(fetch.call_count,1)
            with patch("tools.fetch_salamander_bank_q4._read_url",side_effect=AssertionError("network")):
                self.assertEqual(install_one(root,"C4v12.flac",sha,len(pcm)),"reused")
            self.assertEqual((root/"Samples/C4v12.flac").read_bytes(),pcm)

    def test_corrupt_replacement_is_detected_and_never_installed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            file=root/"Samples/C4v12.flac"
            file.parent.mkdir()
            file.write_bytes(b"existing old file")
            old=file.read_bytes()
            with patch("tools.fetch_salamander_bank_q4._read_url",
                       return_value=b"invalid content"):
                with self.assertRaisesRegex(ValueError,"Wrong byte count"):
                    install_one(root,"C4v12.flac","0"*40,999,retries=1)
            self.assertEqual(file.read_bytes(),old)
            self.assertFalse((root/"Samples/C4v12.flac.part").exists())

    def test_path_traversal_and_bad_download_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ("../evil.flac","some/subdir.flac","",".."):
                with self.assertRaises(ValueError):
                    install_one(Path(tmp),name,"a"*40,10,retries=1)
            with patch("tools.fetch_salamander_bank_q4._read_url",
                       return_value=b"eight-bytes"):
                with self.assertRaisesRegex(ValueError,"digest mismatch"):
                    install_one(Path(tmp),"C4v1.flac","f"*40,11,retries=1)


if __name__=="__main__":
    unittest.main()
