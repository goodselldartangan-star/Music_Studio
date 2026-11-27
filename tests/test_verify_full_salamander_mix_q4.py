"""Q4 full-bank verifier: fail closed on provenance and double-pedal sounds."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import soundfile as sf

from tools.verify_full_salamander_mix_q4 import run,SR


class FullBankSafetyTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root=Path(self.t.name)
        self.lanes=self.root/"lanes"
        self.lanes.mkdir()
        (self.lanes/"voice_program").mkdir()
        (self.lanes/"voice_program/Q4_voice_only.sfz").write_text(
            "<group>\n<region> sample=C4v12.flac\n")
        (self.lanes/"Q4_lane_plan.json").write_text(json.dumps({
            "duration_s":1.,
            "lane_plan":{"input_notes":64},
            "renders":[{"wav":"0"},{"wav":"1"}]}))
        (self.lanes/"Q4_pedal_route_plan.json").write_text(json.dumps({
            "shared_mechanism_instances":1,"cc64_movement_count":16}))
        self.source=self.root/"source.json"
        self.source.write_text(json.dumps({
            "blob_sha_verified_count":641,
            "total_unique_original_flacs":641,
            "git_tree_total_bytes":748397030,
            "pinned_commit":"sample-commit",
            "license":"CC BY 3.0 - Alexander Holm"}))
        t=np.arange(SR)/SR
        data=np.stack([.05*np.sin(2*np.pi*220*t),
                       .04*np.sin(2*np.pi*220*t)],axis=1)
        for name,gain in (("with_pedal_lane_00",1.),
                          ("with_pedal_lane_01",.3),
                          ("shared_pedal",.03)):
            sf.write(self.lanes/f"{name}.wav",data*gain,SR,subtype="PCM_24")

    def test_full_report_requires_valid_source_identity(self):
        d=json.loads(self.source.read_text())
        d["blob_sha_verified_count"]=5
        self.source.write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError,"byte-for-byte"):
            run(self.lanes,out=self.root/"out",source_report=self.source)

    def test_cannot_mix_pedal_noise_containing_voice_program(self):
        file=self.lanes/"voice_program/Q4_voice_only.sfz"
        file.write_text('#include "Data/pedal.txt"')
        with self.assertRaisesRegex(ValueError,"mechanical pedal"):
            run(self.lanes,out=self.root/"out",source_report=self.source)

    def test_linear_mix_has_safe_derived_preview_and_one_shared_pedal(self):
        with patch("tools.verify_full_salamander_mix_q4.subprocess.run"):
            result=run(self.lanes,out=self.root/"out",source_report=self.source)
        self.assertEqual(result["voice_instance_count"],2)
        self.assertEqual(result["physical_pedal_mechanism_instances"],1)
        self.assertEqual(result["cc64_pedal_movements"],16)
        self.assertTrue(result["preview_pcm_peak"]<.84)
        self.assertGreater(result["preview_stereo_side_rms"],0)
        self.assertTrue((self.root/"out/Q4_full_piano_audio_verification.json").exists())
        self.assertFalse((self.root/"out/Q4_Silver_full_original_Salamander_preview.wav").exists())


if __name__=="__main__":
    unittest.main()
