"""Q4: CC64-style score note-off deferral is bounded, opt-in and independent."""
import unittest
from copy import deepcopy

from studio7.score import make,validate
from studio7.audit import review
from studio7.pedal_timing import (apply_piano_pedal_windows,
                                  atmospheric_pedal_windows,
                                  shape_silver_pedal_timing)


def piano(pitch,beat,length,velocity=78):
    return {'instrument':'piano','pitch':pitch,'beat':beat,
            'length':length,'velocity':velocity}


class SustainTimingTests(unittest.TestCase):
    def test_only_key_releases_inside_pedal_window_are_held(self):
        score={'bars':16,'notes':[
            piano(60,.20,.25),  # key-up before pedal-down
            piano(62,1.15,.40), # key-up inside window; delay to pedal-up
            piano(64,2.9,.40),  # key-up after pedal-up; unchanged
            dict(instrument='bass',pitch=40,beat=1.15,length=.40,velocity=80)
        ],'drums':[dict(kind='kick',beat=1,velocity=80)]}
        frozen=deepcopy(score)
        shaped,report=apply_piano_pedal_windows(score,[(1.,3.)])
        self.assertEqual(score,frozen)
        self.assertEqual(shaped['notes'][0],score['notes'][0])
        self.assertAlmostEqual(shaped['notes'][1]['beat']+shaped['notes'][1]['length'],3.,places=4)
        self.assertEqual(shaped['notes'][2],score['notes'][2])
        self.assertEqual(shaped['notes'][3],score['notes'][3])
        self.assertEqual(shaped['drums'],score['drums'])
        self.assertEqual(report['piano_notes_held_past_key_release'],1)
        self.assertFalse(report['true_pedal_mechanism_or_string_resonance'])

    def test_repeated_same_pitch_stays_independently_overlapping(self):
        score={'bars':16,'notes':[
            piano(60,.15,.42,90),
            piano(60,.80,.20,59),
            piano(64,1.05,.28,76)]}
        shaped,report=apply_piano_pedal_windows(score,[(.05,1.8)])
        self.assertEqual(report['piano_notes_held_past_key_release'],3)
        self.assertEqual([n['pitch'] for n in score['notes']],
                         [n['pitch'] for n in shaped['notes']])
        self.assertEqual([n['beat'] for n in score['notes']],
                         [n['beat'] for n in shaped['notes']])
        self.assertEqual([n['velocity'] for n in score['notes']],
                         [n['velocity'] for n in shaped['notes']])
        self.assertGreater(shaped['notes'][0]['beat']+shaped['notes'][0]['length'],
                           shaped['notes'][1]['beat'])
        self.assertEqual([round(n['beat']+n['length'],4) for n in shaped['notes']],
                         [1.8,1.8,1.8])

    def test_silver_pattern_is_safely_separated_between_chord_changes(self):
        original=make('silver')
        before=deepcopy(original)
        windows=atmospheric_pedal_windows(original)
        self.assertEqual(len(windows),8)
        for (start,end),(next_start,_) in zip(windows,windows[1:]):
            self.assertLess(end,next_start)
            self.assertGreater(next_start-end,.10)
        changed,report=shape_silver_pedal_timing(original)
        self.assertEqual(original,before)
        self.assertEqual(shape_silver_pedal_timing(original),(changed,report))
        self.assertGreater(report['piano_notes_held_past_key_release'],0)
        self.assertLess(report['max_noteoff_extension_beats'],1.5)
        self.assertEqual(len(original['notes']),len(changed['notes']))
        self.assertEqual(original['drums'],changed['drums'])
        for old,new in zip(original['notes'],changed['notes']):
            self.assertEqual((old['beat'],old['pitch'],old['velocity'],old['instrument']),
                             (new['beat'],new['pitch'],new['velocity'],new['instrument']))
            self.assertGreaterEqual(new['length'],old['length'])
            if old['instrument']!='piano' or old['beat']<32:
                self.assertEqual(old,new)
        self.assertTrue(validate(changed)['validated'])
        self.assertTrue(review(changed)['passed'])

    def test_respects_explicit_pedal_ignore(self):
        score={'bars':16,'notes':[dict(**piano(60,1.,.5),pedal='ignore')]}
        changed,report=apply_piano_pedal_windows(score,[(.5,3.)])
        self.assertEqual(changed,score)
        self.assertEqual(report['piano_notes_held_past_key_release'],0)

    def test_bad_or_unterminated_windows_rejected(self):
        score={'bars':16,'notes':[piano(60,.1,.5)]}
        for windows in ([(-.1,2.)],[(0.,64.)],[(1.,1.)],[(1.,2.),(1.99,3.)],
                        [(0.,float('nan'))],[(2.,float('inf'))]):
            with self.subTest(windows=windows), self.assertRaises(ValueError):
                apply_piano_pedal_windows(score,windows)
        with self.assertRaisesRegex(ValueError,'Silver-only'):
            atmospheric_pedal_windows(make('harbor'))


if __name__=='__main__':
    unittest.main()
