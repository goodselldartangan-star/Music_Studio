"""Q4 in-context comparison rejects wrong score, clipped or incomplete piano."""
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import soundfile as sf

from tools.compare_pianos_in_mix_q4 import load_original_grand_lanes, rms
from studio7.effects import SR


class InContextPianoTests(unittest.TestCase):
    def test_three_independent_source_streams_sum_with_correct_stereo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"Q4_lane_plan.json").write_text(json.dumps({
                "lane_plan":{"input_notes":64,"instance_count":2}}))
            (root/"Q4_pedal_route_plan.json").write_text(json.dumps({
                "shared_mechanism_instances":1,"cc64_movement_count":16}))
            t=np.arange(SR)/SR
            a=np.stack([.06*np.sin(2*np.pi*220*t),
                        .045*np.sin(2*np.pi*220*t)],axis=1)
            for i,v in (("with_pedal_lane_00",1.),
                        ("with_pedal_lane_01",.3),
                        ("shared_pedal",.03)):
                sf.write(root/f"{i}.wav",a*v,SR,subtype="PCM_24")
            actual=load_original_grand_lanes(root,frames=SR)
            self.assertEqual(actual.shape,(SR,2))
            self.assertLess(abs(rms(actual)-rms(a*1.33)),.00001)
            self.assertGreater(float(np.max(np.abs(actual[:,0]-actual[:,1]))),.005)

    def test_source_guard_refuses_missing_pedal_or_wrong_instance_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"Q4_lane_plan.json").write_text(json.dumps({
                "lane_plan":{"input_notes":64,"instance_count":1}}))
            (root/"Q4_pedal_route_plan.json").write_text(json.dumps({
                "shared_mechanism_instances":1,"cc64_movement_count":16}))
            with self.assertRaisesRegex(ValueError,"Silver"):
                load_original_grand_lanes(root,frames=SR)


if __name__=="__main__":
    unittest.main()
