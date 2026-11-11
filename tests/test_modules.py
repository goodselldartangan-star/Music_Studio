"""Focused interface tests: changing one subsystem shouldn't break another."""
import math
from pathlib import Path
import tempfile
import unittest
import numpy as np
import mido
from studio3.spec import Settings,Note,SR,BARS,SECTIONS
from studio3.composition import create_score,CHORDS,HOOK
from studio3.instruments import hz,note_wave,plucked_string,drum_wave
from studio3.midi import write_midi,PROGRAMS
from studio3.mix import insert,oversampled_saturation


class ScoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.full=create_score()

    def test_contiguous_sections(self):
        self.assertEqual(SECTIONS[0][0],0)
        self.assertEqual(SECTIONS[-1][1],BARS)
        self.assertTrue(all(a[1]==b[0] for a,b in zip(SECTIONS,SECTIONS[1:])))
    def test_all_sections_and_chords(self):
        s=self.full
        self.assertEqual(len(s['chords']),BARS)
        self.assertGreaterEqual(len(set(c['chord'] for c in s['chords'])),5)
        self.assertTrue(all(c['chord'] in CHORDS for c in s['chords']))
        self.assertGreater(len(s['notes']),2300)
        self.assertGreater(len(s['drums']),900)
    def test_score_notes_are_valid(self):
        for n in self.full['notes']:
            self.assertTrue(20<=n['pitch']<=108)
            self.assertTrue(0<=n['beat']<BARS*4)
            self.assertTrue(.02<=n['duration']<=8)
            self.assertTrue(0<n['velocity']<=1.1)
    def test_hook_repeats_and_returns(self):
        notes=self.full['notes']
        pitches=lambda bar:[n['pitch'] for n in notes if n['part']=='lead' and bar*4<=n['beat']<(bar+1)*4]
        self.assertEqual(pitches(32),pitches(40))
        self.assertEqual(pitches(32),pitches(80))
        self.assertTrue(any(n['part']=='counter' for n in notes))
    def test_independent_configuration(self):
        original=create_score(Settings(preview_bars=3))
        variant=create_score(Settings(tempo:=103,transpose=-2,seed=333,preview_bars=3))
        self.assertEqual(original['bars'],3)
        self.assertEqual(variant['bpm'],tempo)
        self.assertEqual([n['pitch']-v['pitch'] for n,v in zip(original['notes'],variant['notes'])],[2]*len(original['notes']))
        self.assertNotEqual(original['notes'],variant['notes'])
        self.assertAlmostEqual(variant['duration_seconds'],3*4*60/103+3)
    def test_invalid_controls_fail_before_render(self):
        for settings in (dict(bpm=89),dict(bpm=146),dict(transpose=-6),dict(transpose=6),dict(preview_bars=0),dict(preview_bars=105)):
            with self.assertRaises(ValueError):Settings(**settings)
    def test_deterministic_score(self):
        self.assertEqual(create_score(Settings(preview_bars=8)),create_score(Settings(preview_bars=8)))
    def test_preview_matches_full(self):
        first=create_score(Settings(preview_bars=8))
        self.assertEqual(first['notes'],[n for n in self.full['notes'] if n['beat']<32])
        self.assertEqual(first['drums'],[n for n in self.full['drums'] if n['beat']<32])


class SynthesisTests(unittest.TestCase):
    def test_all_synth_parts(self):
        for p in ('pluck','bass','keys','pad','arp','lead','counter','bell'):
            n=Note(p,0,.8,66,.6)
            y=note_wave(n,118,123)
            self.assertGreater(len(y),1000)
            self.assertTrue(np.isfinite(y).all())
            self.assertGreater(np.max(abs(y)),0)
    def test_string_determinism(self):
        a=plucked_string(62,.8,.6,55);b=plucked_string(62,.8,.6,55)
        self.assertTrue(np.array_equal(a,b))
    def test_pitch_accuracy(self):
        for pitch in (45,57,69,81):
            y=plucked_string(pitch,.95,.7,121)
            excerpt=y[round(.12*SR):round(.76*SR)]
            nfft=8*len(excerpt)
            f=np.fft.rfftfreq(nfft,1/SR)
            spec=abs(np.fft.rfft(excerpt*np.hanning(len(excerpt)),nfft))
            target=hz(pitch);mask=(f>.92*target)&(f<1.08*target)
            found=f[mask][np.argmax(spec[mask])]
            self.assertLess(abs(1200*math.log2(found/target)),12)
    def test_pluck_decay(self):
        y=plucked_string(62,1.0,.6,81)
        early=np.sqrt(np.mean(y[round(.015*SR):round(.085*SR)]**2))
        late=np.sqrt(np.mean(y[round(.80*SR):round(.92*SR)]**2))
        self.assertGreater(early,late*2)
    def test_drum_color_variations(self):
        for kind in ('kick','snare','hat','open_hat','shaker','ghost','rim','tom','clap','impact'):
            a=drum_wave(kind,0);b=drum_wave(kind,1)
            self.assertTrue(np.isfinite(a).all())
            self.assertGreater(np.max(abs(a)),0)
            self.assertFalse(np.array_equal(a,b))
    def test_saturator_does_not_create_nans(self):
        t=np.arange(25000)/SR
        y=np.stack([np.sin(2*np.pi*900*t),np.sin(2*np.pi*1200*t)],axis=1).astype(np.float32)
        z=oversampled_saturation(y,1.13)
        self.assertEqual(y.shape,z.shape)
        self.assertTrue(np.isfinite(z).all())
    def test_stereo_pan(self):
        dst=np.zeros((SR,2),np.float32)
        insert(dst,np.ones(800,dtype=np.float32),0,-.7,118)
        self.assertGreater(np.sum(dst[:,0]**2),np.sum(dst[:,1]**2))


class ExportTests(unittest.TestCase):
    def test_midi_tracks_are_independent(self):
        score=create_score(Settings(preview_bars=12))
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'song.mid'
            write_midi(score,target)
            data=mido.MidiFile(target)
            self.assertEqual(len(data.tracks),len(PROGRAMS)+2)
            self.assertGreater(sum(len(t) for t in data.tracks),500)


if __name__=='__main__': unittest.main()
