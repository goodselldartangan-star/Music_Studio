"""P5: recognizable motifs and chord-tone final cadences."""
import unittest
from copy import deepcopy
from studio7.score import make,SONGS,validate,SCALE
from studio7.audit import review
from studio7.melody import shape_final_answer,motif_report


class MelodicAnswerTests(unittest.TestCase):
    def test_reproducible_and_earlier_refrain_preserved(self):
        for style in SONGS:
            old=make(style);untouched=deepcopy(old)
            new,report=shape_final_answer(old)
            self.assertEqual(old,untouched)
            self.assertEqual(shape_final_answer(old),(new,report))
            self.assertTrue(report['changed'])
            self.assertEqual(old['drums'],new['drums'])
            altered=[]
            for i,(a,b) in enumerate(zip(old['notes'],new['notes'])):
                if a!=b:altered.append(i)
                if a['beat']<60:self.assertEqual(a,b)
                self.assertEqual((a['instrument'],a['beat'],a['velocity']),
                                 (b['instrument'],b['beat'],b['velocity']))
                if a['instrument'] not in ('lead','electric'):self.assertEqual(a,b)
            self.assertEqual(len(altered),1)
            changed=new['notes'][altered[0]]
            self.assertIn(changed['pitch']%12,SCALE[style])
            self.assertLess(changed['beat']+changed['length'],64)
            self.assertTrue(validate(new)['validated'])
            self.assertTrue(review(new)['passed'])

    def test_phrase_report_nonempty(self):
        for style in SONGS:
            m=motif_report(make(style))
            self.assertGreater(m['last_refrain_notes'],4)
            self.assertGreater(m['same_pitch_onset_build_to_final'],4)
            self.assertIsNotNone(m['last_note_pitch'])

    def test_fixed_phrase_respected(self):
        score=make('harbor')
        last=max((n for n in score['notes'] if n['instrument']=='electric' and n['beat']>=60),
                 key=lambda n:n['beat'])
        last['technique']='fixed'
        after,report=shape_final_answer(score)
        self.assertEqual(after,score)
        self.assertFalse(report['changed'])

    def test_unsupported_style_rejected(self):
        score=make('harbor');score['style']='missing'
        with self.assertRaises(ValueError):shape_final_answer(score)


if __name__=='__main__':unittest.main()
