"""Q4.2 only explicit original-sample stopped strings change, no voice stealing."""
import unittest

import numpy as np

from studio7.guitar_damping_q42 import (
    TECHNIQUE,damp_note_tail,note_if_tagged,shape_harbor_stopped_upstrokes)
from studio7.score import make


class IndependentStopTests(unittest.TestCase):
    def test_only_explicitly_tagged_harbor_upstrokes_are_selected(self):
        original=make("harbor")
        shaped,stats=shape_harbor_stopped_upstrokes(original)
        self.assertEqual(stats["damped_strokes"],6)
        self.assertEqual(stats["tagged_notes"],24)
        self.assertEqual(stats["chosen_bars"],[4,6,8,10,12,14])
        for a,b in zip(original["notes"],shaped["notes"]):
            for key in ("instrument","pitch","beat","length","velocity"):
                self.assertEqual(a[key],b[key])
            if b.get("technique")==TECHNIQUE:
                self.assertEqual(b["instrument"],"acoustic")
                self.assertNotIn("technique",a)
        self.assertEqual(original["drums"],shaped["drums"])
        self.assertEqual(original["chords"],shaped["chords"])

    def test_untagged_does_not_change_original_note_samples(self):
        x=np.ones((24000,2),np.float32)
        self.assertIs(note_if_tagged(x,{"instrument":"acoustic"}),x)
        self.assertTrue(np.array_equal(x,np.ones_like(x)))

    def test_stopped_pluck_keeps_attack_and_fades_to_exact_silence(self):
        sr=44100
        t=np.arange(sr,dtype=np.float32)/sr
        mono=.3*np.sin(2*np.pi*220*t)
        stereo=np.stack((mono,mono*.6),axis=1)
        y=damp_note_tail(stereo,start_ms=240,fade_ms=42)
        self.assertTrue(np.array_equal(y[:int(.2*sr)],stereo[:int(.2*sr)]))
        self.assertLess(float(np.max(np.abs(y[int(.29*sr):]))),1e-9)
        self.assertLess(float(np.max(np.abs(np.diff(y,axis=0)))),.025)
        self.assertTrue(np.array_equal(stereo[:,0],mono))
        ymono=damp_note_tail(mono,start_ms=240,fade_ms=42)
        self.assertEqual(ymono.ndim,1)

    def test_long_ring_survives_later_short_pluck(self):
        sr=44100
        old=np.full(sr,0.2,dtype=np.float32)
        new=np.full(sr//2,0.18,dtype=np.float32)
        damped=note_if_tagged(new,{"technique":TECHNIQUE,"damp_after_ms":240})
        mix=np.zeros((sr,),np.float32)
        mix[:len(old)]+=old
        at=int(.15*sr)
        mix[at:at+len(new)]+=damped
        self.assertAlmostEqual(float(mix[int(.9*sr)]),.2,places=6)
        self.assertGreater(float(mix[int(.16*sr)]),.2)
        self.assertTrue(np.array_equal(old,np.full(sr,.2,dtype=np.float32)))

    def test_damping_must_have_valid_sample_envelope(self):
        x=np.ones((1000,2),np.float32)
        for kwargs in ({"start_ms":10},{"start_ms":float('nan')},
                       {"start_ms":230,"fade_ms":0},
                       {"start_ms":230,"fade_ms":200}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):
                damp_note_tail(x,**kwargs)
        with self.assertRaises(ValueError):
            damp_note_tail(np.array([float("nan")],np.float32),start_ms=240)

    def test_other_scores_are_untouched(self):
        score=make("silver")
        shaped,stats=shape_harbor_stopped_upstrokes(score)
        self.assertEqual(score,shaped)
        self.assertEqual(stats["tagged_notes"],0)


if __name__=="__main__":
    unittest.main()
