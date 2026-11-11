"""Regression tests for symbolic reasoning, A/B controls and modular boundaries."""
import copy
import unittest
from studio3.composition import create_score, CHORDS
from studio3.spec import Settings
from studio3.theory import CHORD_CLASSES, diatonic_step, verify_chords
from studio3.development import develop_score
from studio3.review import audit_score, bar_signature, section_similarity


class HarmonyTests(unittest.TestCase):
    def test_labels_match_actual_voicing(self):
        verify_chords(CHORDS)
        self.assertEqual(set(CHORDS),set(CHORD_CLASSES))

    def test_misleading_chord_name_rejected(self):
        bad=dict(CHORDS);bad['Bm9']=((59,62,64,69,73),35)
        with self.assertRaisesRegex(ValueError,'pitch classes'):verify_chords(bad)

    def test_diatonic_variations_stay_in_key(self):
        self.assertEqual(diatonic_step(74,1),76)
        self.assertEqual(diatonic_step(74,-1),73)


class DevelopmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=create_score();cls.improved=develop_score(cls.original)
        cls.old_report=audit_score(cls.original,CHORDS)
        cls.new_report=audit_score(cls.improved,CHORDS,strict=True)

    def test_original_score_not_modified(self):
        self.assertNotIn('development',self.original)
        self.assertIn('development',self.improved)

    def test_reproducible_composition(self):
        self.assertEqual(self.improved,develop_score(self.original))

    def test_preserve_hook_identity(self):
        for first,second in [(32,40),(32,80),(40,88)]:
            self.assertEqual(bar_signature(self.improved['notes'],first),
                             bar_signature(self.improved['notes'],second))

    def test_verse_is_meaningfully_developed(self):
        a=self.new_report['phrase_comparisons']['verse_reply']
        b=self.old_report['phrase_comparisons']['verse_reply']
        self.assertLess(a['matches'],b['matches'])
        self.assertLessEqual(a['matches'],7)

    def test_final_chorus_not_a_clone(self):
        a=self.new_report['phrase_comparisons']['chorus_development']
        b=self.old_report['phrase_comparisons']['chorus_development']
        self.assertLess(a['matches'],b['matches'])
        self.assertLessEqual(a['matches'],8)

    def test_out_of_key_notes_fixed(self):
        self.assertGreater(self.old_report['out_of_key_count'],0)
        self.assertEqual(self.new_report['out_of_key_count'],0)

    def test_original_bass_and_drums_preserved(self):
        self.assertEqual(self.original['drums'],self.improved['drums'])
        self.assertEqual([n for n in self.original['notes'] if n['part']=='bass'],
                         [n for n in self.improved['notes'] if n['part']=='bass'])

    def test_sections_midi_contract_unchanged(self):
        self.assertEqual(self.original['sections'],self.improved['sections'])
        self.assertEqual(self.original['chords'],self.improved['chords'])
        self.assertEqual(self.original['bars'],self.improved['bars'])

    def test_variations_do_not_shift_notes_out_of_bar(self):
        for n in self.improved['notes']:
            self.assertGreaterEqual(n['beat'],0)
            self.assertLess(n['beat'],self.improved['bars']*4)
            self.assertGreater(n['duration'],0)
            self.assertGreaterEqual(n['pitch'],20)
            self.assertLessEqual(n['pitch'],108)

    def test_preview_is_prefix_of_full(self):
        small=develop_score(create_score(Settings(preview_bars=12)))
        notes=[n for n in self.improved['notes'] if n['beat']<48]
        self.assertEqual(small['notes'],notes)
        self.assertEqual(small['drums'],[d for d in self.improved['drums'] if d['beat']<48])

    def test_transposition_retains_harmonic_audit(self):
        alt=develop_score(create_score(Settings(transpose=-3,preview_bars=32)))
        self.assertEqual(audit_score(alt,CHORDS,strict=True)['out_of_key_count'],0)

    def test_audit_warns_about_repeated_choruses(self):
        report=self.old_report
        self.assertTrue(any('chorus_development' in w for w in report['warnings']))
        with self.assertRaisesRegex(ValueError,'Composition preflight'):
            audit_score(self.original,CHORDS,strict=True)


if __name__=='__main__':unittest.main()
