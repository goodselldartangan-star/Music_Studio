"""P3 cross-contract: drum accents and bass anchor timing remain separable."""
import unittest
from copy import deepcopy
from studio7.score import make,SONGS
from studio7.drum_dynamics import shape_drum_dynamics
from studio7.rhythm import shape_pocket


class RhythmCrossContracts(unittest.TestCase):
    def test_drum_velocity_and_bass_anchor_timing_commute(self):
        for name in SONGS:
            src=make(name);saved=deepcopy(src)
            a=shape_pocket(shape_drum_dynamics(src)[0])[0]
            b=shape_drum_dynamics(shape_pocket(src)[0])[0]
            self.assertEqual(a,b)
            self.assertEqual(src,saved)
            self.assertEqual(len(src['notes']),len(a['notes']))
            self.assertEqual(len(src['drums']),len(a['drums']))
            for x,y in zip(src['notes'],a['notes']):
                self.assertEqual((x['instrument'],x['pitch'],x['velocity'],x['length']),
                                 (y['instrument'],y['pitch'],y['velocity'],y['length']))
                if x['instrument']!='bass':self.assertEqual(x,y)
            for x,y in zip(src['drums'],a['drums']):
                self.assertEqual((x['beat'],x['kind']), (y['beat'],y['kind']))

    def test_intentional_pickup_not_attracted_to_backbeat(self):
        src=make('after')
        y=shape_pocket(shape_drum_dynamics(src)[0])[0]
        for x,n in zip(src['notes'],y['notes']):
            if x['instrument']=='bass' and x['beat']%4 >= .38:
                self.assertEqual(x,n)


if __name__=='__main__':unittest.main()
