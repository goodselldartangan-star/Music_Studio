"""P4: verify chord spelling and bounded foreground/piano octave separation."""
import unittest
from copy import deepcopy
from unittest.mock import patch
from studio7.score import make,SONGS,validate
from studio7.audit import review
from studio7.registers import audit_registers,separate_lead_piano


class RegistersP4(unittest.TestCase):
    def test_chord_labels_voicings_and_bass_roots(self):
        for style in SONGS:
            s=make(style);a=audit_registers(s)
            self.assertEqual(len(a['chords']),4)
            self.assertEqual([x['name'] for x in a['chords']],list(SONGS[style]['harmonies']))
        wrong=deepcopy(SONGS['after'])
        wrong['roots']=(41,)+tuple(wrong['roots'][1:])
        with patch.dict(SONGS,{'after':wrong}):
            with self.assertRaises(ValueError):
                audit_registers(make('harbor')|{'style':'after'})

    def test_revoicing_preserves_pitch_classes_melody_notes_and_durations(self):
        for style in SONGS:
            src=make(style);saved=deepcopy(src)
            rev,report=separate_lead_piano(src)
            self.assertEqual(src,saved)
            self.assertEqual(separate_lead_piano(src),(rev,report))
            self.assertGreater(report['piano_chord_groups_revoiced'],0)
            self.assertGreater(report['unisons_before'],report['unisons_after'])
            self.assertLessEqual(report['semitones_after'],report['semitones_before'])
            self.assertEqual(src['drums'],rev['drums'])
            self.assertEqual(src['chords'],rev['chords'])
            self.assertEqual(len(src['notes']),len(rev['notes']))
            for x,y in zip(src['notes'],rev['notes']):
                self.assertEqual((x['beat'],x['length'],x['velocity'],x['instrument']),
                                 (y['beat'],y['length'],y['velocity'],y['instrument']))
                if x['instrument']=='piano':
                    self.assertIn(x['pitch']-y['pitch'],(0,12))
                    self.assertEqual(x['pitch']%12,y['pitch']%12)
                    self.assertTrue(48<=y['pitch']<=108)
                else:self.assertEqual(x,y)
            self.assertTrue(validate(rev)['validated'])
            self.assertTrue(review(rev)['passed'],review(rev))

    def test_atmospheric_piano_lead_unison_reduction(self):
        old=make('silver');new,rep=separate_lead_piano(old)
        self.assertGreaterEqual(rep['unisons_before'],16)
        self.assertEqual(rep['unisons_after'],0)
        self.assertGreater(rep['piano_notes_revoiced'],10)

    def test_intentional_fixed_register_not_revoiced(self):
        score=make('silver')
        for n in score['notes']:
            if n['instrument']=='piano':n['register']='fixed'
        updated,rep=separate_lead_piano(score)
        self.assertEqual(score,updated)
        self.assertEqual(rep['piano_notes_revoiced'],0)

    def test_invalid_chord_spelling_or_voicing_rejected(self):
        original=deepcopy(SONGS['harbor'])
        original['harmonies']=('D','Gmaj7','Bm','G')
        with patch.dict(SONGS,{'harbor':original}):
            with self.assertRaises(ValueError):audit_registers(make('harbor'))


if __name__=='__main__':unittest.main()
