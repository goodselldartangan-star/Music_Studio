"""Q4.3 bass-only in-context experimental source replacement guardrails."""
import tempfile
import unittest
from pathlib import Path

import numpy as np
import soundfile as sf

from studio7.score import make
from studio7.effects import SR
from tools.compare_fashionbass_in_mix_q43 import load_original_bass_stem,rms


class BassStemGuardTests(unittest.TestCase):
    def test_accept_only_exact_original_score_length(self):
        score=make("harbor")
        length=round(score["duration"]*SR)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"bass.wav"
            t=np.arange(length,dtype=np.float32)/SR
            stereo=np.stack((.02*np.sin(2*np.pi*82*t),
                             .019*np.sin(2*np.pi*82*t)),axis=1)
            sf.write(path,stereo,SR,subtype="PCM_24")
            restored=load_original_bass_stem(path,score)
            self.assertEqual(restored.shape,(length,2))
            self.assertGreater(rms(restored),.001)
            self.assertGreater(float(np.max(np.abs(restored[:,0]-restored[:,1]))),.0001)
            original=make("harbor")
            self.assertEqual(score,original)

    def test_reject_wrong_sampler_rate_or_wrong_duration(self):
        score=make("harbor")
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"bass.wav"
            sample=np.full((SR,2),.001,np.float32)
            sf.write(path,sample,SR)
            with self.assertRaisesRegex(ValueError,"malformed"):
                load_original_bass_stem(path,score)
            sf.write(path,sample,48000)
            with self.assertRaisesRegex(ValueError,"malformed"):
                load_original_bass_stem(path,score)

    def test_zero_source_cannot_be_a_valid_backend(self):
        score=make("harbor")
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"bass.wav"
            # No audio is a failure, not a silently normalized source.
            sf.write(path,np.zeros((round(score["duration"]*SR),2),np.float32),SR)
            with self.assertRaisesRegex(ValueError,"malformed"):
                load_original_bass_stem(path,score)


if __name__=="__main__":
    unittest.main()
