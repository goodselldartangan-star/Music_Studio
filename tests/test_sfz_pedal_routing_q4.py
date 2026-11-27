"""Q4 pure SFZ pedal movement routing independent of MIDI synthesis."""
import unittest

from studio7.sfz_pedal_routing import pedal_controllers
from studio7.score import make
from studio7.pedal_timing import atmospheric_pedal_windows


class IndependentMechanismTests(unittest.TestCase):
    def test_two_piano_lanes_receive_cc64_but_only_one_mechanism_instance(self):
        a=pedal_controllers([(1.,2.),(3.,4.)],
                            duration_beats=8,lanes=2)
        self.assertEqual(a["mechanism_instances"],1)
        self.assertEqual(a["pedal_movement_count"],4)
        self.assertEqual(len(a["note_lane_events"]),2)
        self.assertEqual(a["note_lane_events"][0],a["note_lane_events"][1])
        for voice in a["note_lane_events"]:
            self.assertEqual(voice[0],(0.,22,0))
            self.assertEqual(voice[1:],a["single_mechanism_events"][1:])
        self.assertEqual(a["single_mechanism_events"][0],(0.,22,64))

    def test_silver_authored_pedal_windows_route_16_edges_once(self):
        score=make('silver')
        report=pedal_controllers(
            atmospheric_pedal_windows(score),
            duration_beats=score['bars']*4,lanes=2)
        self.assertEqual(report["pedal_movement_count"],16)
        self.assertEqual(len(report["single_mechanism_events"]),17)
        self.assertTrue(report["suppressed_in_note_lanes"])

    def test_bad_events_are_rejected(self):
        for windows in ([(-1.,2.)],[(1.,1.)],[(1.,12.)],
                        [(0.,3.),(2.,5.)],[(1.,float('nan'))],
                        [(2.,float('inf'))]):
            with self.subTest(windows=windows),self.assertRaises(ValueError):
                pedal_controllers(windows,duration_beats=10,lanes=2)
        with self.assertRaises(ValueError):
            pedal_controllers([],duration_beats=0,lanes=2)
        with self.assertRaises(ValueError):
            pedal_controllers([],duration_beats=10,lanes=0)


if __name__=="__main__":
    unittest.main()
