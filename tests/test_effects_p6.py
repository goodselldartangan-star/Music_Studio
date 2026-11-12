"""P6 effects acceptance: controlled wet-only room and tempo delay."""
import unittest
import numpy as np
from studio7.effects import SR,room_send,tap_delay,mono_below


class RoomSpaceTests(unittest.TestCase):
    def setUp(self):
        self.x=np.zeros((SR,2),np.float32)
        self.x[round(.05*SR),:]=.5

    def test_zero_wet_is_exact_silence(self):
        y=room_send(self.x,wet=0)
        self.assertEqual(y.shape,self.x.shape)
        self.assertEqual(float(np.max(abs(y))),0.)

    def test_predelay_moves_only_room_reflections(self):
        base=room_send(self.x,wet=.24,predelay_ms=0)
        target=room_send(self.x,wet=.24,predelay_ms=35)
        shift=round(.035*SR)
        self.assertTrue(np.isfinite(target).all())
        # The optional room delay should shift the *wet* sound, not the dry note.
        self.assertLess(float(np.max(abs(target[:shift]))),1e-6)
        np.testing.assert_allclose(target[shift:],base[:-shift],atol=2e-6)
        self.assertGreater(float(np.max(abs(target))),1e-4)
        self.assertGreater(float(np.max(abs(base[:,0]-base[:,1]))),1e-5)

    def test_default_is_equal_to_explicit_zero_predelay(self):
        np.testing.assert_array_equal(room_send(self.x,wet=.13),
                                      room_send(self.x,wet=.13,predelay_ms=0))

    def test_invalid_room_controls_are_rejected(self):
        for args in ({'wet':-1},{'wet':float('nan')},{'ir_seconds':.07},
                     {'ir_seconds':5},{'predelay_ms':-1},{'predelay_ms':300}):
            with self.subTest(args=args),self.assertRaises(ValueError):
                room_send(self.x,**args)

    def test_bad_stereo_and_nonfinite_input_are_rejected(self):
        with self.assertRaises(ValueError):room_send(np.ones((500,1),np.float32))
        invalid=self.x.copy();invalid[25,0]=np.nan
        with self.assertRaises(ValueError):room_send(invalid)

    def test_tempo_delay_timing_and_clean_zero_wet(self):
        impulse=self.x
        clean=tap_delay(impulse,120,wet=0,beat_fraction=.5)
        np.testing.assert_array_equal(clean,impulse)
        slow=tap_delay(impulse,120,beat_fraction=.5,wet=.4,stereo=False)
        fast=tap_delay(impulse,240,beat_fraction=.5,wet=.4,stereo=False)
        lag_slow=round(.25*SR);lag_fast=round(.125*SR)
        t=round(.05*SR)
        self.assertGreater(float(np.max(abs(slow[t+lag_slow:t+lag_slow+500]-impulse[t+lag_slow:t+lag_slow+500]))),.001)
        self.assertGreater(float(np.max(abs(fast[t+lag_fast:t+lag_fast+500]-impulse[t+lag_fast:t+lag_fast+500]))),.001)

    def test_mono_below_does_not_change_shape_or_create_nonfinite(self):
        t=np.arange(SR,dtype=np.float32)/SR
        x=np.stack([.1*np.sin(2*np.pi*60*t),-.1*np.sin(2*np.pi*60*t)],axis=1)
        mono=mono_below(x,150)
        self.assertEqual(mono.shape,x.shape)
        self.assertTrue(np.isfinite(mono).all())
        # The current 2-pole crossover reduces low side energy, but is not a
        # brickwall mono filter. Stronger sub isolation belongs to P7.
        self.assertLess(float(np.sqrt(np.mean(mono**2))),float(np.sqrt(np.mean(x**2)))*.7)


if __name__=='__main__':unittest.main()
