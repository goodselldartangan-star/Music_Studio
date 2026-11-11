"""Offline unit tests for the original v2 renderer; no AI or network."""
import math
import tempfile
import unittest
from pathlib import Path
import numpy as np
import mido
import studio_v2 as v


class CompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.score=v.song_plan()

    def test_contiguous_section_map(self):
        a=v.SECTIONS
        self.assertEqual(a[0][0],0)
        self.assertEqual(a[-1][1],v.BARS)
        self.assertTrue(all(x[1]==y[0] for x,y in zip(a,a[1:])))

    def test_chords_are_supported_and_have_diversity(self):
        self.assertEqual(len(self.score['chords']),v.BARS)
        self.assertGreaterEqual(len(set(c['chord'] for c in self.score['chords'])),7)
        self.assertTrue(all(c['chord'] in v.CHORDS for c in self.score['chords']))

    def test_notes_and_drums_are_complete(self):
        self.assertGreater(len(self.score['notes']),2000)
        self.assertGreater(len(self.score['drums']),1000)
        self.assertTrue(all(28<=n['pitch']<=100 for n in self.score['notes']))
        self.assertIn('bridge',[x['name'] for x in self.score['sections']])

    def test_motif_returns_with_variation(self):
        notes=self.score['notes']
        first=[n['pitch'] for n in notes if n['part']=='lead' and 28*4 <= n['beat'] < 29*4]
        later=[n['pitch'] for n in notes if n['part']=='lead' and 36*4 <= n['beat'] < 37*4]
        final=[n['pitch'] for n in notes if n['part']=='lead' and 72*4 <= n['beat'] < 73*4]
        self.assertEqual(first,later)
        self.assertEqual(first,final)
        self.assertGreater(len([n for n in notes if n['part']=='reply']),0)

    def test_composition_is_deterministic(self):
        self.assertEqual(self.score,v.song_plan())

    def test_preview_does_not_change_opening(self):
        short=v.song_plan(8)
        original=[n for n in self.score['notes'] if n['beat']<32]
        self.assertEqual(short['notes'],original)
        self.assertEqual(short['bars'],8)

    def test_tempo_key_and_seed_are_real_controls(self):
        altered=v.song_plan(8,bpm=103,transpose=-3,seed=4321)
        base=v.song_plan(8)
        self.assertEqual(altered['bpm'],103)
        self.assertEqual(altered['transpose'],-3)
        self.assertAlmostEqual(altered['duration_seconds'],8*4*60/103+v.TAIL)
        self.assertTrue(all(a['pitch']-b['pitch']==-3 for a,b in zip(altered['notes'],base['notes'])))
        self.assertNotEqual(altered['notes'],v.song_plan(8,bpm=103,transpose=-3,seed=8888)['notes'])

    def test_invalid_tempo_and_transpose_rejected(self):
        for bpm in (89,146):
            with self.assertRaises(ValueError):v.song_plan(4,bpm=bpm)
        for transpose in (-6,6):
            with self.assertRaises(ValueError):v.song_plan(4,transpose=transpose)

    def test_bad_preview_rejected(self):
        for bars in (0,89,-1):
            with self.assertRaises(ValueError):v.song_plan(bars)

    def test_midi_is_playable(self):
        with tempfile.TemporaryDirectory() as temp:
            f=Path(temp)/'score.mid'
            v.write_midi(self.score,f)
            mid=mido.MidiFile(f)
            self.assertEqual(len(mid.tracks),10)
            self.assertGreater(sum(map(len,mid.tracks)),4800)


class DSPTests(unittest.TestCase):
    def test_plucked_string_is_finite_and_reproducible(self):
        a=v.string_wave(57,.6,seed=123)
        b=v.string_wave(57,.6,seed=123)
        self.assertTrue(np.array_equal(a,b))
        self.assertTrue(np.isfinite(a).all())
        self.assertGreater(np.max(np.abs(a)),.05)

    def test_string_pitch_accuracy(self):
        for pitch in (45,57,69,81):
            a=v.string_wave(pitch,.85,seed=42)
            excerpt=a[int(.10*v.SR):int(.70*v.SR)]
            nfft=8*len(excerpt)
            spectrum=np.abs(np.fft.rfft(excerpt*np.hanning(len(excerpt)),n=nfft))
            axis=np.fft.rfftfreq(nfft,1/v.SR)
            target=v.hz(pitch)
            mask=(axis>.92*target)&(axis<1.08*target)
            actual=axis[mask][np.argmax(spectrum[mask])]
            self.assertLess(abs(1200*math.log2(actual/target)),10,pitch)

    def test_oversampling_reduces_high_frequency_alias(self):
        from scipy.signal import periodogram
        time=np.arange(int(.30*v.SR))/v.SR
        fundamental=8000
        original=np.sin(2*np.pi*fundamental*time)
        raw=np.tanh(original*2.8)/np.tanh(2.8)
        cleaner=v.soft_clip_oversampled(original[:,None].astype(np.float32),2.8)[:,0]
        freq,pow_raw=periodogram(raw,v.SR)
        _,pow_clean=periodogram(cleaner,v.SR)
        alias=int(3*fundamental-v.SR)  # |24k - 44.1k| = 20.1k
        idx=np.argmin(np.abs(freq-abs(alias)))
        reduction_db=10*math.log10((pow_clean[idx]+1e-15)/(pow_raw[idx]+1e-15))
        self.assertLess(reduction_db,-10)

    def test_plucked_string_has_decay(self):
        a=v.string_wave(57,.9,seed=9)
        first=np.sqrt(np.mean(a[int(.02*v.SR):int(.10*v.SR)]**2))
        last=np.sqrt(np.mean(a[int(.70*v.SR):int(.80*v.SR)]**2))
        self.assertGreater(first,3*last)

    def test_synthesis_voices(self):
        for part in ('pluck','bass','keys','pad','arp','bell','lead','reply'):
            a=v.voice_wave(v.Note(part,0,.75,69,.65))
            self.assertTrue(np.isfinite(a).all(),part)
            self.assertGreater(np.max(np.abs(a)),.005,part)

    def test_drums_vary_but_repeat_deterministically(self):
        for kind in ('kick','snare','ghost','clap','hat','open_hat','rim','tom','impact'):
            wave=v.drum_wave(kind,4)
            self.assertTrue(np.isfinite(wave).all(),kind)
            self.assertGreater(np.max(np.abs(wave)),.001,kind)
            self.assertTrue(np.array_equal(wave,v.drum_wave(kind,4)),kind)

    def test_oversampling_is_finite_and_not_extreme(self):
        x=np.sin(np.linspace(0,20,10000,dtype=np.float32)).reshape(-1,1)
        y=v.soft_clip_oversampled(x)
        self.assertEqual(y.shape,x.shape)
        self.assertTrue(np.isfinite(y).all())
        self.assertLess(np.max(np.abs(y)),1.1)

    def test_stereo_pan_and_bus_eq(self):
        bus=np.zeros((10000,2),np.float32)
        v.stereo_add(bus,np.ones(500,np.float32),.03,-.5)
        self.assertGreater(np.sum(abs(bus[:,0])),np.sum(abs(bus[:,1])))
        for kind in ('drums','bass','strings','keys','lead'):
            y=v.apply_bus_eq(kind,bus)
            self.assertTrue(np.isfinite(y).all())


if __name__=='__main__':unittest.main()