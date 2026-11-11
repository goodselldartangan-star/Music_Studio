"""P2 regression: musical strums while other notes and voices keep ringing."""
import unittest
from copy import deepcopy
from studio7.score import make,SONGS,validate
from studio7.playing import shape_strums
from studio7.audit import review


class GuitarStrumTests(unittest.TestCase):
    def test_each_style_reproducible_and_score_compatible(self):
        for style in SONGS:
            original=make(style)
            before=deepcopy(original)
            after, report=shape_strums(original)
            self.assertEqual(original,before)
            self.assertEqual(shape_strums(original),(after,report))
            self.assertGreater(report['strum_groups'],0,style)
            self.assertLess(report['max_onset_shift_ms'],32)
            self.assertEqual(len(after['notes']),len(original['notes']))
            self.assertEqual(after['drums'],original['drums'])
            for old,new in zip(original['notes'],after['notes']):
                self.assertEqual((old['pitch'],old['length'],old['instrument']),
                                 (new['pitch'],new['length'],new['instrument']))
                if old['instrument'] not in ('acoustic','electric'):
                    self.assertEqual(old,new)
                self.assertLessEqual(abs(new['velocity']-old['velocity']),5)
                self.assertTrue(0<=new['beat']<64)
            self.assertTrue(validate(after)['validated'])
            self.assertTrue(review(after)['passed'],(style,review(after)))

    def test_down_upstrokes_keep_earlier_strings_ringing(self):
        score={'bpm':120,'notes':[
            dict(instrument='acoustic',pitch=p,beat=b,length=1.5,velocity=80)
            for p,b in zip((52,55,59,64),(.10,.14,.18,.22))
        ]+[
            dict(instrument='acoustic',pitch=p,beat=b,length=.7,velocity=65)
            for p,b in zip((64,59,55,52),(2.10,2.14,2.18,2.22))
        ],'drums':[]}
        out,report=shape_strums(score)
        self.assertEqual((report['downstrokes'],report['upstrokes']),(1,1))
        self.assertEqual(out['notes'][0]['beat'],.1)
        self.assertEqual(out['notes'][4]['beat'],2.1)
        self.assertLess(out['notes'][0]['beat'],out['notes'][1]['beat'])
        self.assertGreater(out['notes'][0]['beat']+out['notes'][0]['length'],
                           out['notes'][3]['beat'])

    def test_explicit_block_chords_and_solo_notes_unchanged(self):
        score={'bpm':110,'notes':[
            dict(instrument='electric',pitch=p,beat=1.,length=1.,velocity=80)
            for p in (60,64,67)
        ]+[dict(instrument='electric',pitch=71,beat=2.5,length=.8,velocity=73)],'drums':[]}
        out,report=shape_strums(score)
        self.assertEqual(out,score)
        self.assertEqual(report['changed_notes'],0)

if __name__=='__main__':unittest.main()
