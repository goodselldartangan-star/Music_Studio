"""Q4 standalone per-instance MIDI lanes and lossless linear summing."""
import json
import tempfile
import unittest
from pathlib import Path

import mido
import numpy as np
import soundfile as sf

from tools.render_sfz_lanes_q4 import SR,prepare,combine,FIXTURE
from studio7.score import make


class IsolatedSfizzAudioTests(unittest.TestCase):
    def test_two_replucks_are_placed_in_different_instance_midi_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)
            report=prepare(dest,FIXTURE,120.,4.)
            self.assertEqual(report['lane_plan']['lane_per_original_note'],[0,1])
            self.assertEqual(report['lane_plan']['instance_count'],2)
            for entry in report['renders']:
                midi=mido.MidiFile(dest/entry['midi'])
                played=[msg for msg in midi.tracks[0]
                        if msg.type=='note_on' and msg.note==60]
                self.assertEqual(len(played),1)
                marker=[msg for msg in midi.tracks[0]
                        if msg.type=='note_on' and msg.note==1]
                self.assertEqual(len(marker),1)

    def test_lane_mix_is_linear_and_preserves_original_old_voice(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)
            plan=prepare(dest,FIXTURE,120.,4.)
            t=np.arange(4*SR)/SR
            old=np.zeros((len(t),2),dtype=np.float32)
            new=np.zeros_like(old)
            old[:,0]=.13*np.sin(2*np.pi*220*t)
            old[:,1]=.11*np.sin(2*np.pi*220*t)
            mask=(t>=.9)&(t<=1.15)
            new[mask]=.03
            for entry,audio in zip(plan['renders'],(old,new)):
                sf.write(dest/entry['wav'],audio,SR,subtype='PCM_24')
            result=combine(dest)
            self.assertEqual(result['rendered_instances'],2)
            y,_=sf.read(dest/'Q4_isolated_lane_mix.wav',always_2d=True)
            self.assertLess(float(np.max(np.abs(y-old-new))),1e-5)
            self.assertGreater(float(np.sqrt(np.mean(y[int(1.4*SR):]**2))),.01)
            self.assertTrue((dest/'Q4_lane_audio_report.json').exists())

    def test_bad_audio_or_insufficient_capacity_fails_before_release(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)
            with self.assertRaisesRegex(ValueError,'pool'):
                prepare(dest,FIXTURE,120.,4.,max_instances=1)
            with self.assertRaisesRegex(ValueError,'room for'):
                prepare(dest,[dict(FIXTURE[0],length=8.)],120.,4.)
            plan=prepare(dest,FIXTURE,120.,4.)
            for entry in plan['renders']:
                sf.write(dest/entry['wav'],np.zeros((SR//2,2)),SR)
            with self.assertRaisesRegex(ValueError,'truncated'):
                combine(dest)

    def test_full_silver_notes_have_a_valid_bounded_render_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            score=make('silver')
            notes=[n for n in score['notes'] if n['instrument']=='piano']
            result=prepare(Path(tmp),notes,score['bpm'],score['duration'])
            self.assertEqual(result['lane_plan']['input_notes'],len(notes))
            self.assertLessEqual(result['lane_plan']['instance_count'],8)
            self.assertEqual(len(list(Path(tmp).glob('lane_*.mid'))),
                             result['lane_plan']['instance_count'])


if __name__=="__main__":
    unittest.main()
