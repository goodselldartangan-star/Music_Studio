"""P5 descriptive phrase audit and intentional cadence tests."""
import unittest
from copy import deepcopy
from studio7.score import make, SONGS
from studio7.melody import shape_final_answer,FINAL_ANSWERS
from tools.audit_phrases_p5 import phrase_metrics,audit_all


class PhraseAuditTests(unittest.TestCase):
    def test_three_distinct_sections_reported_without_score_change(self):
        for style in SONGS:
            score=make(style)
            frozen=deepcopy(score)
            report=phrase_metrics(score)
            self.assertEqual(score,frozen)
            self.assertEqual(list(report['passages']),['16','32','48'])
            self.assertTrue(all(v['notes']>0 for v in report['passages'].values()))
            self.assertTrue(all(v['longest_note_beats']>0 for v in report['passages'].values()))
            self.assertEqual(sum(v['notes'] for v in report['passages'].values()),
                             sum(n['instrument'] in ('lead','electric') and n['length']>.5
                                 and 16<=n['beat']<64 for n in score['notes']))

    def test_optional_answer_preserves_earlier_phrase_and_notes(self):
        for style in SONGS:
            score=make(style)
            before=phrase_metrics(score)
            after_score,change=shape_final_answer(score)
            after=phrase_metrics(after_score)
            self.assertEqual(before['passages']['16'],after['passages']['16'])
            self.assertEqual(before['passages']['32'],after['passages']['32'])
            self.assertTrue(change['changed'])
            self.assertEqual(sum(a!=b for a,b in zip(score['notes'],after_score['notes'])),1)
            self.assertEqual(after['motif']['last_note_pitch'],FINAL_ANSWERS[style][0])

    def test_final_answer_lands_in_last_chord(self):
        for style in SONGS:
            score=make(style)
            candidate,_=shape_final_answer(score)
            pitch=phrase_metrics(candidate)['motif']['last_note_pitch']
            # Last 4-bar harmonic cycle ends on the fourth score voicing.
            from studio7.score import SONGS as DATA
            self.assertIn(pitch%12,{p%12 for p in DATA[style]['voicings'][-1]})

    def test_audit_all_complete_without_audio(self):
        data=audit_all()
        self.assertEqual(set(data),set(SONGS))
        self.assertTrue(all(x['change']['earlier_hook_unchanged'] for x in data.values()))


if __name__=='__main__':unittest.main()
