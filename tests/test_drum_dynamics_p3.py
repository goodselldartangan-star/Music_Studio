"""P3 regression: drum velocity phrasing must preserve original patterns."""
import unittest
from copy import deepcopy
from studio7.score import make, SONGS, validate
from studio7.audit import review
from studio7.drum_dynamics import shape_drum_dynamics


class DrumDynamicsTests(unittest.TestCase):
    def test_all_styles_pure_and_valid(self):
        for style in SONGS:
            score = make(style)
            baseline = deepcopy(score)
            revised, info = shape_drum_dynamics(score)
            self.assertEqual(score, baseline)
            self.assertEqual(shape_drum_dynamics(score), (revised, info))
            self.assertGreater(info['hits'], 10)
            self.assertGreater(info['changed'], 10)
            self.assertLessEqual(info['max_velocity_delta'], 9)
            self.assertEqual(revised['notes'], score['notes'])
            self.assertEqual(len(revised['drums']), len(score['drums']))
            for a,b in zip(score['drums'], revised['drums']):
                self.assertEqual((a['beat'],a['kind']), (b['beat'],b['kind']))
                self.assertLessEqual(abs(a['velocity']-b['velocity']), 9)
            self.assertTrue(validate(revised)['validated'])
            self.assertTrue(review(revised)['passed'])

    def test_backbeat_phrase_and_hat_interaction(self):
        s={'bpm':120,'drums':[
            dict(kind='kick',beat=12.,velocity=85),
            dict(kind='snare',beat=15.,velocity=80),
            dict(kind='hat',beat=15.,velocity=47),
            dict(kind='hat',beat=15.5,velocity=43)],'notes':[]}
        y,r=shape_drum_dynamics(s)
        self.assertEqual(y['drums'][1]['velocity'],86)
        self.assertEqual(y['drums'][2]['velocity'],43)
        self.assertEqual(y['drums'][3]['velocity'],43)
        self.assertEqual(s['drums'][1]['velocity'],80)

    def test_explicit_ghost_fixed_remain_untouched(self):
        s={'bpm':115,'drums':[
            dict(kind='snare',beat=1.3,velocity=24,technique='ghost'),
            dict(kind='hat',beat=1.5,velocity=51,technique='fixed')],'notes':[]}
        result,rep=shape_drum_dynamics(s)
        self.assertEqual(result,s)
        self.assertEqual(rep['changed'],0)

    def test_no_new_drum_hits(self):
        s={'bpm':115,'drums':[],'notes':[]}
        result,rep=shape_drum_dynamics(s)
        self.assertEqual(result,s)
        self.assertEqual(rep['hits'],0)

    def test_reject_out_of_range_velocity(self):
        s={'bpm':120,'drums':[dict(kind='kick',beat=0.,velocity=155)],'notes':[]}
        with self.assertRaises(ValueError):shape_drum_dynamics(s)

if __name__=='__main__': unittest.main()
