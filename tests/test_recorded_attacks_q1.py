"""Q1: distinguish measurable leading silence from note duration/articulation."""
import tempfile
import unittest
from pathlib import Path

import numpy as np
import soundfile as sf

from studio6.soundfonts import SR
from tools.audit_recorded_attacks_q1 import onset_ms, examine_file, audit_collection, audit_all


def recording(delay_ms: float, duration_s: float=.5, volume:float=.2):
    frames=round(duration_s*SR)
    t=np.arange(frames)/SR
    delay=round(delay_ms/1000*SR)
    x=np.zeros(frames,dtype=np.float32)
    played=t[:frames-delay]
    x[delay:]=(volume*np.sin(2*np.pi*440*played)*(1-np.exp(-played*120))).astype(np.float32)
    return x


class SourceAttackTests(unittest.TestCase):
    def test_known_early_and_late_recorded_attacks(self):
        early=recording(8.)
        late=recording(68.)
        a=onset_ms(early,SR)
        b=onset_ms(late,SR)
        self.assertIsNotNone(a)
        self.assertIsNotNone(b)
        self.assertLess(abs(a-8),8)
        self.assertLess(abs(b-68),8)
        self.assertGreater(b-a,54)

    def test_detectors_are_read_only_for_mono_and_stereo(self):
        x=recording(33)
        saved=x.copy()
        stereo=np.stack([x*.9,x*.4],axis=1)
        self.assertLess(abs(onset_ms(x,SR)-onset_ms(stereo,SR)),3)
        np.testing.assert_array_equal(x,saved)

    def test_silence_and_invalid_waveforms(self):
        self.assertIsNone(onset_ms(np.zeros(SR//3,dtype=np.float32),SR))
        with self.assertRaises(ValueError):
            onset_ms(np.array([0,np.nan],dtype=np.float32),SR)
        with self.assertRaises(ValueError):
            onset_ms(recording(10),123)

    def test_real_file_inventory_flags_inconsistent_layers_without_edits(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for name in ('meta-steel-guitar','meta-piano','meta-nylon-guitar'):
                folder=root/name
                folder.mkdir()
                for i,delay in enumerate((8,67),start=1):
                    sf.write(folder/f'INSPiano_Vel0{i}_Gs5_01.wav',
                             recording(delay),SR)
            sample=root/'meta-piano'/'INSPiano_Vel02_Gs5_01.wav'
            before=sample.read_bytes()
            measured=examine_file(sample)
            self.assertEqual(measured['channels'],1)
            self.assertGreater(measured['onset_ms'],60)
            report=audit_all(root)
            for name,c in report['collections'].items():
                self.assertEqual(c['recordings'],2)
                self.assertEqual(c['within_string_layer_spread_over_25ms_count'],1)
                if name=='meta-piano':
                    self.assertEqual(c['late_review_count'],1)
            self.assertEqual(sample.read_bytes(),before)

    def test_different_guitar_strings_do_not_create_false_layer_outliers(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            folder=root/'meta-steel-guitar'
            folder.mkdir()
            # Identical pitches can occur on very different physical strings.
            # Their absolute onsets may differ. Compare only within the same
            # physical string when assessing velocity-layer inconsistency.
            for zone,delay in [('A',6),('B',36)]:
                for layer in (1,2):
                    sf.write(folder/f'INSGuitarSteel_String{zone}_Vel0{layer}_C4_01.wav',
                             recording(delay),SR)
            report=audit_collection(root,'meta-steel-guitar')
            self.assertEqual(report['recordings'],4)
            self.assertEqual(report['within_string_layer_spread_over_25ms_count'],0)

    def test_missing_library_is_an_error_not_a_mono_fallback(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(FileNotFoundError):
                audit_collection(Path(temp),'meta-piano')


if __name__=='__main__':
    unittest.main()
