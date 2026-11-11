"""Regression gates for note lifecycles, voice retriggering and natural releases."""
from pathlib import Path
import unittest
import numpy as np
from studio7.articulation import (PROFILES,smooth_release,planned_events,
                                  assign_voice_channels,render_polyphonic)
from studio6.soundfonts import FluidSynth, SR

FONT=Path('/usr/share/sounds/sf2/TimGM6mb.sf2')

class ArticulationTests(unittest.TestCase):
    def test_smooth_note_end_preserves_attack_and_longer_tail(self):
        raw=np.full(SR*2,.32,dtype=np.float32)
        y=smooth_release(raw,.35,part='piano')
        self.assertAlmostEqual(float(y[int(.14*SR)]),.32,places=5)
        self.assertGreater(float(y[int(.46*SR)]),.20)
        self.assertLess(float(y[-1]),.00001)
        boundary=int(.35*SR)
        self.assertLess(abs(float(y[boundary])-float(y[boundary-1])),.0001)
    def test_part_specific_release_is_not_global(self):
        raw=np.ones(2*SR,dtype=np.float32)
        short=smooth_release(raw,.5,part='bass')
        long=smooth_release(raw,.5,part='piano')
        self.assertGreater(len(long),len(short))
    def test_explicit_rest_remains(self):
        notes=[{'beat':0,'length':.7,'pitch':69,'velocity':85},
               {'beat':2.0,'length':.7,'pitch':71,'velocity':82}]
        events=planned_events(notes,120,part='lead')
        self.assertLess(events[0]['off'],events[1]['at'])
    def test_near_touching_melodic_notes_connect_but_piano_does_not(self):
        notes=[{'beat':0,'length':.9,'pitch':69,'velocity':85},
               {'beat':1.0,'length':.9,'pitch':71,'velocity':82}]
        lead=planned_events(notes,120,part='lead')
        piano=planned_events(notes,120,part='piano')
        self.assertGreater(lead[0]['off'],lead[1]['at'])
        self.assertLess(piano[0]['off'],piano[1]['at'])
    def test_retriggered_same_pitch_uses_an_independent_voice(self):
        notes=[{'beat':0,'length':1.5,'pitch':64,'velocity':98},
               {'beat':1.0,'length':1.5,'pitch':64,'velocity':93}]
        events=assign_voice_channels(planned_events(notes,120,part='electric'))
        self.assertNotEqual(events[0]['channel'],events[1]['channel'])
    def test_large_polyphonic_chord_uses_shared_channel(self):
        # 40 distinct simultaneous pitches must not waste all 15 melodic channels.
        notes=[{'at':0.,'off':1.,'pitch':40+i,'velocity':70} for i in range(40)]
        events=assign_voice_channels(notes)
        self.assertEqual(len(events),40)
        self.assertEqual({e['channel'] for e in events},{0})
    def test_polyphonic_chord_retrigger_uses_only_needed_channels(self):
        notes=[{'at':0.,'off':1.,'pitch':60+i,'velocity':80} for i in range(5)]
        notes += [{'at':.5,'off':1.5,'pitch':60+i,'velocity':80} for i in range(5)]
        events=assign_voice_channels(notes,release_guard_s=.2)
        self.assertEqual({x['channel'] for x in events[:5]},{0})
        self.assertEqual({x['channel'] for x in events[5:]},{1})
    def test_retrigger_guard_and_channel_reuse(self):
        notes=[{'at':0.,'off':.4,'pitch':64,'velocity':80},
               {'at':.65,'off':.9,'pitch':64,'velocity':85},
               {'at':.7,'off':1.0,'pitch':64,'velocity':95},
               {'at':1.1,'off':1.3,'pitch':64,'velocity':60}]
        channels=[e['channel'] for e in assign_voice_channels(notes,release_guard_s=.2)]
        self.assertEqual(channels,[0,0,1,0])
    def test_dense_real_soundfont_piano_chord(self):
        if not FONT.is_file():self.skipTest('No local GM soundfont')
        notes=[{'beat':0.,'length':2.,'pitch':50+i,'velocity':72} for i in range(20)]
        y=render_polyphonic(FONT,notes,2.0,120,part='piano',program=0)
        self.assertEqual(y.shape,(2*SR,2))
        self.assertTrue(np.isfinite(y).all())
        self.assertGreater(float(np.max(np.abs(y))),1e-3)
    def test_overcapacity_raises_instead_of_silent_steal(self):
        notes=[{'at':0.,'off':2.,'pitch':60,'velocity':80} for i in range(16)]
        with self.assertRaisesRegex(ValueError,'simultaneous'):
            assign_voice_channels(notes)
    def test_soundfont_overlapping_retrigger_is_audio_distinct(self):
        if not FONT.is_file():self.skipTest('No local GM soundfont')
        notes=[{'beat':0.,'length':1.8,'pitch':64,'velocity':100},
               {'beat':1.,'length':1.8,'pitch':64,'velocity':100},
               {'beat':2.,'length':1.8,'pitch':64,'velocity':100}]
        fs=FluidSynth(FONT,gain=.33,drum=False)
        try:
            self.assertEqual(fs.select(fs.synth,0,fs.id,0,25),0)
            old=fs.render([{'at':n['beat']*.5,'off':(n['beat']+n['length'])*.5,
                            'pitch':n['pitch'],'velocity':n['velocity']} for n in notes],round(3.0*SR))
        finally:fs.close()
        new=render_polyphonic(FONT,notes,3.,120,part='electric',program=25)
        self.assertEqual(old.shape,new.shape)
        self.assertTrue(np.isfinite(new).all())
        self.assertGreater(float(np.max(np.abs(new-old))),.004)
        # In the old implementation, noteOff #1 can prematurely stop note #2.
        # Test this is not a no-op; rely on the audio difference, not a taste score.
        lo,hi=round(.95*SR),round(1.07*SR)
        self.assertGreater(float(np.sqrt(np.mean(new[lo:hi]**2))),.0001)

if __name__=='__main__':unittest.main()
