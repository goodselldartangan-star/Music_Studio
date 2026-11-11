"""No cloud calls: composition/engine tests for the fully local instrumental."""
import json
import math
import tempfile
import unittest
from pathlib import Path

import numpy as np
import mido
import offline_song as studio


class LocalMusicTests(unittest.TestCase):
    def setUp(self):
        studio.arrange()

    def test_section_map_is_contiguous(self):
        sections=studio.SEC
        self.assertEqual(sections[0][0],0)
        self.assertEqual(sections[-1][1],studio.BARS)
        self.assertTrue(all(a[1]==b[0] for a,b in zip(sections,sections[1:])))
        self.assertGreaterEqual(len(sections),8)

    def test_every_bar_has_a_valid_harmony(self):
        self.assertEqual(len([studio.chord(b) for b in range(studio.BARS)]),100)
        self.assertTrue(all(studio.chord(b) in studio.CHORDS for b in range(studio.BARS)))

    def test_original_motif_is_recurring(self):
        self.assertEqual(len(studio.HOOK),8)
        n=[x for x in studio.notes if x.voice=='lead' and 32*4<=x.beat<48*4]
        self.assertGreater(len(n),45)
        self.assertEqual([x.pitch for x in n if x.beat<33*4],
                         [x.pitch for x in n if 40*4<=x.beat<41*4])

    def test_composition_is_reproducible(self):
        a=([(n.voice,n.beat,n.pitch,n.vel) for n in studio.notes],
           [(h.kind,h.beat,h.vel) for h in studio.hits])
        studio.arrange()
        b=([(n.voice,n.beat,n.pitch,n.vel) for n in studio.notes],
           [(h.kind,h.beat,h.vel) for h in studio.hits])
        self.assertEqual(a,b)
        self.assertGreater(len(studio.notes),2500)
        self.assertGreater(len(studio.hits),1200)

    def test_voices_produce_finite_nonsilent_sound(self):
        for voice in ['bass','pluck','keys','pad','arp','lead','counter','glow']:
            wave=studio.synth(studio.Note(voice,0,.45,69,.6))
            self.assertTrue(np.isfinite(wave).all(),voice)
            self.assertGreater(float(np.max(np.abs(wave))),.004,voice)

    def test_every_drum_can_be_rendered(self):
        for kind in ['kick','snare','clap','closed_hat','open_hat','rim','tom','ghost','impact']:
            wave=studio.drum_wave(kind,0)
            self.assertTrue(np.isfinite(wave).all(),kind)
            self.assertGreater(len(wave),200)
            self.assertGreater(float(np.max(np.abs(wave))),.001,kind)

    def test_midi_writes_and_reads(self):
        with tempfile.TemporaryDirectory() as t:
            f=Path(t)/'test.mid'
            studio.as_midi(f)
            mid=mido.MidiFile(f)
            self.assertEqual(len(mid.tracks),10)
            self.assertGreater(sum(len(tr) for tr in mid.tracks),4000)


if __name__=='__main__':unittest.main()
