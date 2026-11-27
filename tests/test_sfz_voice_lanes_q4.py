"""Q4 pure SFZ voice-instance planning, not a sampler implementation."""
from copy import deepcopy
import unittest

from studio7.sfz_voice_lanes import assign_sfz_voice_lanes
from studio7.score import make
from studio7.pedal_timing import shape_silver_pedal_timing


def note(p,beat,dur,vel=80):
    return {"instrument":"piano","pitch":p,"beat":beat,"length":dur,"velocity":vel}


class SfizzInstancePlanningTests(unittest.TestCase):
    def test_chord_shares_one_instance_and_repluck_goes_to_another(self):
        scored=[note(60,.1,2.0),note(64,.11,1.7),
                note(67,.12,1.6),note(60,.8,.18)]
        original=deepcopy(scored)
        lanes,report=assign_sfz_voice_lanes(scored,120)
        self.assertEqual(report['instance_count'],2)
        self.assertEqual(report['lane_per_original_note'],[0,0,0,1])
        self.assertEqual([len(g) for g in lanes],[3,1])
        self.assertEqual(scored,original)

    def test_release_guard_retains_old_ring_and_allows_later_reuse(self):
        notes=[note(60,0.,1.),note(60,1.1,.3),note(60,2.5,.1)]
        lanes,report=assign_sfz_voice_lanes(notes,60,release_guard_s=.5)
        self.assertEqual(report['lane_per_original_note'],[0,1,0])
        self.assertEqual(len(lanes),2)

    def test_simultaneous_three_same_pitch_notes_require_three_instances(self):
        notes=[note(60,1.,2.,velocity) for velocity in (50,75,120)]
        lanes,report=assign_sfz_voice_lanes(notes,120,max_instances=3)
        self.assertEqual(report['lane_per_original_note'],[0,1,2])
        self.assertEqual(sum(len(x) for x in lanes),3)
        with self.assertRaisesRegex(ValueError,"refusing to steal"):
            assign_sfz_voice_lanes(notes,120,max_instances=2)

    def test_full_original_and_pedalled_silver_schedules_preserve_all_events(self):
        score=make('silver')
        pedalled,_=shape_silver_pedal_timing(score)
        for variant in (score,pedalled):
            piano=[n for n in variant['notes'] if n['instrument']=='piano']
            frozen=deepcopy(piano)
            lanes,report=assign_sfz_voice_lanes(
                piano,variant['bpm'],max_instances=8)
            self.assertEqual(report['input_notes'],len(piano))
            self.assertEqual(sum(len(group) for group in lanes),len(piano))
            self.assertEqual(piano,frozen)
            self.assertLessEqual(report['instance_count'],8)
            self.assertGreaterEqual(report['instance_count'],1)
            # All original notes survive, including the intentionally
            # independently overlapping same-pitch retriggers.
            flattened=[n for group in lanes for n in group]
            for original in piano:
                self.assertIn(original,flattened)

    def test_bad_audio_constraints_are_rejected_not_silently_shortened(self):
        valid=[note(60,.1,.5)]
        for params in (dict(bpm=0),dict(bpm=float('nan')),
                       dict(bpm=120,release_guard_s=-1),
                       dict(bpm=120,release_guard_s=10),
                       dict(bpm=120,max_instances=0)):
            with self.subTest(params=params),self.assertRaises(ValueError):
                assign_sfz_voice_lanes(valid,**params)
        for invalid in (note(60,.2,0),note(135,1,.3),
                        note(60,float("nan"),.5),note(60,.1,.2,0)):
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):
                assign_sfz_voice_lanes([invalid],120)


if __name__=="__main__":
    unittest.main()
