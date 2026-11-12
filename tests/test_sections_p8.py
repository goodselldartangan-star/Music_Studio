"""P8 section inventory and opt-in quiet transition regression."""
import unittest
from copy import deepcopy
from studio7.score import make,SONGS,validate
from studio7.audit import review
from studio7.sections import section_inventory,shape_transition_breath


class SectionTests(unittest.TestCase):
    def test_inventory_accounts_for_all_original_events(self):
        for style in SONGS:
            score=make(style)
            before=deepcopy(score)
            report=section_inventory(score)
            self.assertEqual(score,before)
            self.assertEqual(report['note_onsets_total'],len(score['notes']))
            self.assertEqual(report['drum_onsets_total'],len(score['drums']))
            self.assertEqual(set(report['sections']),{'intro','verse','build','final'})
            self.assertGreater(report['sections']['final']['notes'],0)

    def test_each_original_style_only_loses_late_backing_attacks(self):
        for style in SONGS:
            original=make(style)
            untouched=deepcopy(original)
            revised,report=shape_transition_breath(original)
            self.assertEqual(original,untouched)
            self.assertEqual(shape_transition_breath(original),(revised,report))
            self.assertGreaterEqual(len(report['dropped_closed_hats']),1)
            self.assertLessEqual(len(report['dropped_short_bass_pickups']),1)
            self.assertEqual(len(revised['notes']),
                             len(original['notes'])-len(report['dropped_short_bass_pickups']))
            self.assertEqual(len(revised['drums']),
                             len(original['drums'])-len(report['dropped_closed_hats']))
            for n in original['notes']:
                if n['instrument']!='bass':
                    self.assertIn(n,revised['notes'])
            for hit in original['drums']:
                if hit['kind']!='hat' or not 47.35<=hit['beat']<48:
                    self.assertIn(hit,revised['drums'])
            self.assertEqual(revised['chords'],original['chords'])
            self.assertTrue(validate(revised)['validated'])
            self.assertTrue(review(revised)['passed'],(style,review(revised)))

    def test_long_ringing_melody_is_not_choked(self):
        score=make('silver')
        old=[n for n in score['notes'] if n['instrument']=='electric'
             and 44<=n['beat']<48]
        newer,_=shape_transition_breath(score)
        new=[n for n in newer['notes'] if n['instrument']=='electric'
             and 44<=n['beat']<48]
        self.assertEqual(old,new)

    def test_absent_transition_hat_fails_explicitly(self):
        score=make('harbor')
        score['drums']=[d for d in score['drums'] if d['kind']!='hat' or d['beat']<47.35]
        with self.assertRaisesRegex(ValueError,'No late closed-hat'):
            shape_transition_breath(score)

if __name__=='__main__':unittest.main()
