"""Q4 reproducible SFZ/MIDI diagnostics, independent of sfizz installation."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import mido
import numpy as np
import soundfile as sf

from tools import probe_sfz_piano_q4 as probe


class SfizzPianoProbeTests(unittest.TestCase):
    def test_midi_fixture_has_independent_new_channel(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"two.mid"
            probe._write_midi(path,probe.CASES["both_split"])
            midi=mido.MidiFile(path)
            events=[msg for msg in midi.tracks[0] if msg.type in ("note_on","note_off") and msg.note==60]
            self.assertEqual([(e.type,e.channel,e.note) for e in events],[
                ("note_on",0,60),("note_on",1,60),
                ("note_off",1,60),("note_off",0,60)])
            self.assertEqual(sum(e.time for e in midi.tracks[0]),3840)
            sentinel=[msg for msg in midi.tracks[0]
                      if msg.type in ("note_on","note_off") and msg.note==1]
            self.assertEqual([(msg.type,msg.channel) for msg in sentinel],
                             [("note_on",9),("note_off",9)])

    def test_sustain_cc64_fixture_has_up_after_down(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"pedal.mid"
            probe._write_midi(path,probe.CASES["pedal"])
            events=[x for x in mido.MidiFile(path).tracks[0]
                    if x.type=="control_change"]
            self.assertEqual([(x.control,x.value,x.channel) for x in events],
                             [(64,127,0),(64,0,0)])

    def test_actual_source_sha_is_verified_not_trusted_from_filename(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"source.flac"
            sr=48000
            t=np.arange(sr,dtype=np.float32)/sr
            sig=np.stack([.1*np.sin(2*np.pi*220*t),
                          .1*np.sin(2*np.pi*250*t)],axis=1)
            sf.write(path,sig,sr,format="FLAC")
            blob=path.read_bytes()
            expected=hashlib.sha1(
                b"blob "+str(len(blob)).encode()+b"\x00"+blob).hexdigest()
            with patch.dict(probe.SAMPLES,{"source.flac":expected},clear=True):
                report=probe.verify_original_samples(Path(tmp))
                self.assertEqual(report["source.flac"]["sample_rate"],48000)
            with patch.dict(probe.SAMPLES,{"source.flac":"0"*40},clear=True):
                with self.assertRaisesRegex(ValueError,"Publisher Git blob"):
                    probe.verify_original_samples(Path(tmp))

    def test_linear_same_pitch_voice_sum_is_distinguished_from_stolen_tail(self):
        sr=44100
        n=sr*4
        t=np.arange(n,dtype=np.float64)/sr
        old=np.stack([.08*np.sin(2*np.pi*220*t),
                      .07*np.sin(2*np.pi*220*t)],axis=1)
        new=np.zeros_like(old)
        at=int(.9*sr)
        end=int(1.3*sr)
        new[at:end]=.05*np.sin(2*np.pi*220*t[at:end])[:,None]
        intact=probe._voice_metrics(old,new,old+new)
        self.assertTrue(intact["nearly_linear_sum"])
        self.assertAlmostEqual(intact["tail_ratio"],1,places=4)
        stolen=(old+new).copy()
        stolen[at:]=new[at:]
        bad=probe._voice_metrics(old,new,stolen)
        self.assertFalse(bad["nearly_linear_sum"])
        self.assertLess(bad["tail_ratio"],.01)

    def test_variants_do_not_claim_to_be_complete_salamander(self):
        self.assertIn("note_polyphony=1",probe.LIMITED)
        self.assertNotIn("note_polyphony=1",probe.BASE)
        self.assertIn("trigger=release",probe.KEY_RELEASE)
        self.assertIn("on_locc64=127",probe.PEDAL)
        self.assertEqual(len(probe.SAMPLES),5)
        self.assertTrue(all(len(sha)==40 for sha in probe.SAMPLES.values()))


if __name__=="__main__":
    unittest.main()
