"""Staged regressions: score -> instruments -> effects -> export."""
import unittest, tempfile
from pathlib import Path
import numpy as np
from studio7.score import make,validate,SONGS
from studio7.audit import review
from studio7.effects import (SR,sidechain_envelope,tap_delay,room_send,
                             tremolo,subtle_chorus,mono_below)
from studio7.render import _target_gain, _render_with_gm,GM_PROGRAM
from studio7.samples import Collection

class SongContract(unittest.TestCase):
 def test_distinct_structures(self):
  seq=[make(k) for k in SONGS]
  self.assertEqual(len({s['bpm'] for s in seq}),3)
  self.assertEqual(len({s['key'] for s in seq}),3)
  self.assertEqual(len({tuple((n['pitch'],n['beat']) for n in s['notes']) for s in seq}),3)
 def test_score_reproducibility(self):
  for name in SONGS:self.assertEqual(make(name),make(name))
 def test_soundness(self):
  for name in SONGS:
   s=make(name)
   self.assertTrue(validate(s)['validated'])
   self.assertTrue(review(s)['passed'],review(s)['issues'])
   self.assertTrue(all(n['velocity'] in range(1,128) for n in s['notes']))
 def test_native_bass_range(self):
  for name in SONGS:
   self.assertLessEqual(max(n['pitch'] for n in make(name)['notes'] if n['instrument']=='bass'),45)
 def test_guitar_register(self):
  s=make('after')
  p=[n['pitch'] for n in s['notes'] if n['instrument']=='electric' and 16<=n['beat']<32]
  self.assertLessEqual(max(p)-min(p),12)
 def test_review_detects_conflict(self):
  s=make('silver')
  lead=next(n for n in s['notes'] if n['instrument']=='electric')
  piano=next(n for n in s['notes'] if n['instrument']=='piano')
  piano['beat']=lead['beat'];piano['pitch']=lead['pitch']+1;piano['length']=1.
  self.assertFalse(review(s)['passed'])
 def test_song_length(self):
  for name in SONGS:
   s=make(name)
   self.assertLessEqual(s['duration'],43)
   self.assertGreater(s['duration'],32)

class AudioDSP(unittest.TestCase):
 def setUp(self):
  t=np.arange(SR,dtype=np.float32)/SR
  self.x=np.stack([.2*np.sin(2*np.pi*440*t),.2*np.sin(2*np.pi*660*t)],axis=1)
 def test_timed_delay_effect(self):
  y=tap_delay(self.x,120,beat_fraction=.5,wet=.3)
  self.assertEqual(y.shape,self.x.shape)
  self.assertTrue(np.isfinite(y).all())
  self.assertGreater(np.mean(np.abs(y-self.x)),.005)
 def test_room_effect(self):
  wet=room_send(self.x,wet=.2)
  self.assertEqual(wet.shape,self.x.shape)
  self.assertGreater(float(np.std(wet)),1e-4)
  self.assertTrue(np.isfinite(wet).all())
 def test_sidechain_envelope(self):
  env=sidechain_envelope(SR,[int(.2*SR)],depth=.3)
  self.assertAlmostEqual(float(env[0]),1)
  self.assertLess(float(env[int(.225*SR)]),.92)
  self.assertAlmostEqual(float(env[int(.75*SR)]),1)
 def test_tremolo(self):
  t=tremolo(self.x,120,depth=.35)
  self.assertGreater(float(np.mean(np.abs(t-self.x))),.001)
 def test_chorus(self):
  t=subtle_chorus(self.x,120,wet=.16)
  self.assertTrue(np.isfinite(t).all())
  self.assertGreater(float(np.mean(np.abs(t-self.x))),.001)
 def test_mono_low(self):
  y=mono_below(self.x,150)
  self.assertTrue(np.isfinite(y).all())
 def test_gain_bounded(self):
  y,g=_target_gain(self.x,-20)
  self.assertTrue(np.isfinite(y).all())
  self.assertGreater(g,0)
 def test_nylon_fixture_sampler(self):
  import soundfile as sf
  with tempfile.TemporaryDirectory() as temp:
   folder=Path(temp)/"meta-nylon-guitar";folder.mkdir()
   tone=np.sin(2*np.pi*82.4*np.arange(SR)/SR).astype(np.float32)*.22
   sf.write(folder/"INSGuitarNylon_StringLowE_Vel01Finger_E2_01.wav",tone,SR)
   bank=Collection(Path(temp),"meta-nylon-guitar")
   y=bank.render(40,80,.5,115,9)
   self.assertGreater(float(np.max(np.abs(y))),.005)
   self.assertTrue(np.isfinite(y).all())
 def test_missing_optional_collection(self):
  with tempfile.TemporaryDirectory() as temp:
   with self.assertRaises(FileNotFoundError):Collection(Path(temp),"meta-nylon-guitar")
 def test_missing_soundfont_errors(self):
  with self.assertRaises(FileNotFoundError):
   _render_with_gm(Path('/missing/soundfont.sf2'),[],1.,120,'bass')
 def test_gm_sample_renderer(self):
  gm=Path('/usr/share/sounds/sf2/TimGM6mb.sf2')
  if not gm.exists():self.skipTest('No local test GM bank')
  y=_render_with_gm(gm,[dict(beat=0.,length=.8,pitch=52,velocity=87)],1.5,110,'piano')
  self.assertEqual(y.shape,(int(1.5*SR),2))
  self.assertGreater(float(np.max(abs(y))),.0001)

if __name__=='__main__':unittest.main()
