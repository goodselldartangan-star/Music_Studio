"""Q3 stereo sampled-note release and old-mono isolation fixtures."""
import tempfile,unittest
from pathlib import Path
import numpy as np
import soundfile as sf
from studio3.spec import SR
from studio7.stereo_wav_q3 import render_stereo_wav_note,_stereo_at_pitch


class StereoWavTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        src_sr=48000;t=np.arange(src_sr,dtype=np.float32)/src_sr
        base=.22*np.sin(2*np.pi*220*t)*np.exp(-t*2)
        self.stereo=np.stack([base,base*.88+ .01*np.sin(2*np.pi*330*t)],axis=1)
        self.path=self.root/'INSGuitarSteel_StringA_Vel02_A3_01.wav'
        sf.write(self.path,self.stereo,src_sr,subtype='PCM_24')

    def test_true_stereo_is_preserved_without_mono_downmix(self):
        y=render_stereo_wav_note(self.path,57,57,90,.5,120,kind='steel')
        self.assertEqual(y.ndim,2);self.assertEqual(y.shape[1],2)
        self.assertEqual(y.shape[0],round((.5*60/120+.24)*SR))
        self.assertGreater(float(np.max(abs(y[:,0]-y[:,1]))),.0005)
        self.assertTrue(np.isfinite(y).all())
        self.assertGreater(float(np.sqrt(np.mean(y**2))),.001)

    def test_replucked_same_pitch_can_overlap_older_release(self):
        held=render_stereo_wav_note(self.path,57,57,90,1.1,120,kind='steel')
        struck=render_stereo_wav_note(self.path,57,57,68,.16,120,kind='steel')
        offset=round(.25*SR)
        mix=np.zeros((max(len(held),len(struck)+offset),2),dtype=np.float32)
        mix[:len(held)]+=held
        mix[offset:offset+len(struck)]+=struck
        np.testing.assert_allclose(mix[:offset],held[:offset])
        np.testing.assert_allclose(mix[offset:offset+len(struck)],
                                   held[offset:offset+len(struck)]+struck)
        self.assertGreater(float(np.max(abs(mix[offset:offset+100]-held[offset:offset+100]))),0)

    def test_stereo_release_preserves_independent_channel_tails(self):
        short=render_stereo_wav_note(self.path,57,57,80,.24,120,kind='piano')
        long=render_stereo_wav_note(self.path,57,57,80,.8,120,kind='piano')
        attack=round(.10*SR)
        np.testing.assert_array_equal(short[:attack],long[:attack])
        self.assertGreater(float(np.max(np.abs(short[:,0]-short[:,1]))),.0001)
        self.assertGreater(float(np.max(np.abs(long[:,0]-long[:,1]))),.0001)
        self.assertTrue(np.isfinite(short).all())
        self.assertTrue(np.isfinite(long).all())

    def test_excessive_retuning_or_mono_source_is_rejected(self):
        with self.assertRaises(ValueError):render_stereo_wav_note(self.path,57,65,90,.5,120,kind='steel')
        mono=self.root/'mono.wav'
        sf.write(mono,self.stereo.mean(axis=1),48000,subtype='PCM_24')
        with self.assertRaisesRegex(ValueError,'stereo 24-bit'):
            render_stereo_wav_note(mono,57,57,90,.5,120,kind='steel')

    def test_deterministic_and_note_length_does_not_change_attack(self):
        shorter=render_stereo_wav_note(self.path,57,57,80,.4,110,kind='nylon')
        longer=render_stereo_wav_note(self.path,57,57,80,.9,110,kind='nylon')
        np.testing.assert_array_equal(shorter[:round(.1*SR)],longer[:round(.1*SR)])
        self.assertIs(_stereo_at_pitch(self.path,57,57),_stereo_at_pitch(self.path,57,57))


if __name__=='__main__':unittest.main()
