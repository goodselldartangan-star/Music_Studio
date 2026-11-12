"""P7 mono translation and objective peak analysis."""
import unittest
import numpy as np
from studio7.effects import SR
from studio7.mix_translation import precise_mono_below,mix_translation_metrics


class TranslationTests(unittest.TestCase):
    def setUp(self):
        self.t=np.arange(SR,dtype=np.float64)/SR

    def test_60hz_antiphase_low_end_becomes_near_mono(self):
        a=(.12*np.sin(2*np.pi*60*self.t)).astype(np.float32)
        x=np.stack([a,-a],axis=1)
        y=precise_mono_below(x,150)
        orig=mix_translation_metrics(x)
        new=mix_translation_metrics(y)
        self.assertGreater(orig['low_side_fraction'],.98)
        self.assertLess(new['low_side_fraction'],.02)
        self.assertLess(float(np.sqrt(np.mean(y**2))),float(np.sqrt(np.mean(x**2)))*.03)

    def test_center_channel_is_preserved_sample_by_sample(self):
        left=.2*np.sin(2*np.pi*130*self.t)+.08*np.sin(2*np.pi*3300*self.t)
        right=.18*np.sin(2*np.pi*130*self.t+.8)-.07*np.sin(2*np.pi*3300*self.t)
        x=np.stack([left,right],axis=1).astype(np.float32)
        y=precise_mono_below(x,160)
        np.testing.assert_allclose(y.mean(axis=1),x.mean(axis=1),atol=1e-7)
        self.assertEqual(y.shape,x.shape)

    def test_high_frequency_side_information_survives(self):
        side=(.11*np.sin(2*np.pi*4000*self.t)).astype(np.float32)
        x=np.stack([side,-side],axis=1)
        y=precise_mono_below(x,150)
        a=float(np.sqrt(np.mean(x**2)))
        b=float(np.sqrt(np.mean(y**2)))
        self.assertLess(abs(b/a-1),.04)

    def test_unchanged_center_is_unchanged_stereo(self):
        mono=(.1*np.sin(2*np.pi*90*self.t)).astype(np.float32)
        x=np.stack([mono,mono],axis=1)
        y=precise_mono_below(x,160)
        np.testing.assert_allclose(y,x,atol=1e-7)

    def test_true_peak_and_mono_metrics_are_finite(self):
        x=np.zeros((SR,2),np.float32)
        x[1000,0]=.5;x[1000,1]=.4
        r=mix_translation_metrics(x)
        self.assertGreaterEqual(r['estimated_true_peak_dbfs'],r['sample_peak_dbfs']-.1)
        self.assertTrue(all(np.isfinite(v) for k,v in r.items() if isinstance(v,(int,float))))
        self.assertLess(r['balance_db'],3)

    def test_bad_inputs_fail_loudly(self):
        x=np.zeros((100,2),np.float32)
        with self.assertRaises(ValueError):precise_mono_below(x,cutoff=-10)
        with self.assertRaises(ValueError):precise_mono_below(x[:2])
        with self.assertRaises(ValueError):mix_translation_metrics(x,true_peak_rate=3)
        with self.assertRaises(ValueError):mix_translation_metrics(x[:2])
        bad=x.copy();bad[0,1]=np.inf
        with self.assertRaises(ValueError):precise_mono_below(bad)


if __name__=='__main__':unittest.main()
