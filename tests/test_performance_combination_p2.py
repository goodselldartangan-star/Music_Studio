"""P2: independent guitar, bass and piano performance module contracts."""
import unittest
from copy import deepcopy
from studio7.score import make,SONGS
from studio7.playing import shape_strums
from studio7.bass_performance import shape_bass
from studio7.piano_performance import shape_piano


class PerformanceSeparationTests(unittest.TestCase):
    def test_independent_transformations_commute(self):
        for style in SONGS:
            score=make(style)
            original=deepcopy(score)
            a=shape_piano(shape_bass(shape_strums(score)[0])[0])[0]
            b=shape_strums(shape_bass(shape_piano(score)[0])[0])[0]
            self.assertEqual(a,b,style)
            self.assertEqual(score,original)
            self.assertEqual(len(a['notes']),len(score['notes']))
            self.assertEqual(a['drums'],score['drums'])
            self.assertEqual([(n['instrument'],n['pitch']) for n in a['notes']],
                             [(n['instrument'],n['pitch']) for n in score['notes']])
            # Explicit MIDI onsets remain exactly written for bass.
            for old,new in zip(score['notes'],a['notes']):
                if old['instrument']=='bass':
                    self.assertEqual(old['beat'],new['beat'])
                if old['instrument']=='piano':
                    self.assertEqual(old['length'],new['length'])
    def test_all_three_transforms_leave_explicit_sound_effects_untouched(self):
        score={'bpm':120,
               'notes':[dict(instrument='bass',pitch=38,beat=.1,length=.5,velocity=75),
                        dict(instrument='lead',pitch=72,beat=.2,length=.5,velocity=90)],
               'drums':[dict(kind='kick',beat=0.,velocity=88)],
               'effects':{'reverb':.22}}
        modified=shape_piano(shape_bass(shape_strums(score)[0])[0])[0]
        self.assertEqual(modified['effects'],score['effects'])
        self.assertEqual(modified['drums'],score['drums'])
        self.assertEqual(modified['notes'][1],score['notes'][1])


if __name__=='__main__':unittest.main()
