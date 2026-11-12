"""P7 signal-only stem coverage, no aesthetic judgement."""
import unittest
import numpy as np
from studio7.effects import SR
from tools.audit_mix_stems_p7 import describe_stem


class MixStemAuditTests(unittest.TestCase):
    def test_subbass_and_mid_spectrum_detected(self):
        t=np.arange(SR,dtype=np.float64)/SR
        for hz,expected in ((60,'sub_bass_35_160'),(1000,'mid_500_2000'),(4000,'presence_2000_8000')):
            x=(.15*np.sin(2*np.pi*hz*t)).astype(np.float32)
            stereo=np.stack([x,x],axis=1)
            data=describe_stem(stereo)
            self.assertGreater(data['band_fraction'][expected],.95,(hz,data))
            self.assertLess(data['rms_dbfs'],-15)
            self.assertGreater(data['rms_dbfs'],-25)

    def test_quiet_track_and_bad_shapes_handled(self):
        y=describe_stem(np.zeros((100,2),np.float32))
        self.assertEqual(y['rms_dbfs'],-120.)
        self.assertEqual(sum(y['band_fraction'].values()),0)
        with self.assertRaises(ValueError):describe_stem(np.zeros((20,1)))
        bad=np.zeros((100,2));bad[0,1]=np.nan
        with self.assertRaises(ValueError):describe_stem(bad)

if __name__=='__main__':unittest.main()
