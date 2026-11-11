"""Small, fast contract tests that run before the expensive synthesis."""
import unittest
import numpy as np
from studio3.radio_composition import compose,CHORDS,KEY_PCS,STEM,SECTIONS
from studio3.radio_quality import audit_score,signature
from studio3.radio_instruments import note_wave,drum_wave
from studio3.spec import Note
from studio3.radio_mix import insert,oversampled_saturation
class RadioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.score=compose()
    def test_form(self):
        self.assertEqual(self.score['bars'],96)
        self.assertEqual(self.score['sections'][-1]['end'],96)
    def test_chorus_early(self):
        self.assertLess(24*4*60/118,60)
    def test_original_chords_in_scale(self):
        self.assertGreaterEqual(len(CHORDS),6)
        for chord,(tones,bass) in CHORDS.items():
            self.assertTrue(all(t%12 in KEY_PCS for t in tones+(bass,)),chord)
    def test_note_ranges(self):
        self.assertTrue(all(20<=n['pitch']<=108 and n['duration']>=.02 for n in self.score['notes']))
    def test_qa_score(self):self.assertTrue(audit_score(self.score)['passed'])
    def test_determinism(self):self.assertEqual(compose(seed=10,bars=6),compose(seed=10,bars=6))
    def test_alt_seed(self):self.assertNotEqual(compose(seed=10,bars=6)['notes'],compose(seed=11,bars=6)['notes'])
    def test_preview(self):
        p=compose(bars=4)
        self.assertEqual(p['notes'],[n for n in self.score['notes'] if n['beat']<16])
    def test_invalid_controls(self):
        for kwargs in [dict(bpm=40),dict(bpm=160),dict(bars=97),dict(bars=-2)]:
            with self.assertRaises(ValueError):compose(**kwargs)
    def test_sound_synth(self):
        for p in ('pluck','bass','keys','pad','arp','lead','counter','bell'):
            wave=note_wave(Note(p,0,.75,73,.6),118,100)
            self.assertTrue(np.isfinite(wave).all(),p)
            self.assertGreater(np.max(np.abs(wave)),.00001,p)
    def test_drums(self):
        for k in ('kick','snare','clap','hat','open_hat','shaker','ghost','rim','tom','impact'):
            w=drum_wave(k,1);self.assertTrue(np.isfinite(w).all());self.assertGreater(len(w),500)
    def test_mixer_pan(self):
        dst=np.zeros((44100,2),np.float32)
        insert(dst,np.ones(500,np.float32),0,-.8,118)
        self.assertGreater(np.sum(dst[:,0]**2),np.sum(dst[:,1]**2))
    def test_saturation(self):
        a=np.ones((2000,2),np.float32)*.1
        b=oversampled_saturation(a)
        self.assertEqual(a.shape,b.shape)
        self.assertTrue(np.isfinite(b).all())
    def test_chorus_development(self):
        self.assertEqual(signature(self.score,24),signature(self.score,60))
        self.assertNotEqual(signature(self.score,27),signature(self.score,63))
if __name__=='__main__':unittest.main()
