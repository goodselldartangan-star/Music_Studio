import unittest,tempfile,shutil
from pathlib import Path
from studio6.score import make,STYLES
from studio6.soundfonts import render_sf2
from studio6.qa import inspect
import numpy as np
import soundfile as sf

class CompositionChecks(unittest.TestCase):
 def test_distinct_compositions(self):
  scores=[make(x) for x in STYLES]
  self.assertEqual(len({s['key'] for s in scores}),3)
  self.assertGreater(len({tuple(n['pitch'] for n in s['notes'] if n['instrument']=='electric') for s in scores}),1)
  for s in scores:
   self.assertTrue(s['drums'])
   self.assertTrue(all(0<=n['beat']<s['bars']*4 and n['length']>0 for n in s['notes']))
 def test_reproducible(self):
  self.assertEqual(make('porch'),make('porch'))
 def test_bass_guitar_drum_layers(self):
  for x in STYLES:
   s=make(x)
   self.assertTrue(any(n['instrument']=='bass' for n in s['notes']))
   self.assertTrue(any(h['kind']=='kick' for h in s['drums']))
 def test_bad_style(self):
  with self.assertRaises(ValueError):make('random')

class SoundFontChecks(unittest.TestCase):
 def test_missing_font_fails(self):
  with self.assertRaises(FileNotFoundError):render_sf2(Path('/no/such/font.sf2'),[],.5,120)
 def test_recorded_synthesis_audio(self):
  font=Path('/usr/share/sounds/sf2/TimGM6mb.sf2')
  if not font.exists():self.skipTest('Platform has no test SF2')
  y=render_sf2(font,[{'beat':0,'length':1,'pitch':60,'velocity':105}],1.5,120)
  self.assertEqual(y.shape[1],2)
  self.assertTrue(np.isfinite(y).all())
  self.assertGreater(abs(y).max(),.001)

if __name__=='__main__':unittest.main()
