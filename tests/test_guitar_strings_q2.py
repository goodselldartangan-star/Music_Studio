"""Q2 string identity and chord-source collision inspection."""
import tempfile
import unittest
from pathlib import Path
from studio7.score import make
from tools.audit_guitar_strings_q2 import string_of,strum_groups,audit_score


class GuitarStringAuditTests(unittest.TestCase):
    def test_string_zone_recognizes_publisher_recording_filenames(self):
        names={"LowE":"INSGuitarSteel_StringLowE_Vel01_E2_01.ogg",
               "A":"INSGuitarSteel_StringA_Vel02_Fs3_01.wav",
               "D":"INSGuitarNylon_StringD_Vel03Pick_C4_01.ogg",
               "HighE":"INSGuitarSteel_StringHighE_Vel01_Fs4_01.ogg"}
        for zone,name in names.items():
            self.assertEqual(string_of(Path(name)),zone)
        with self.assertRaises(ValueError):
            string_of(Path("piano_Vel01_C4.wav"))

    def test_existing_acoustic_strum_groups_are_detected(self):
        for style in ("harbor","silver"):
            groups=strum_groups(make(style)["notes"])
            self.assertGreater(len(groups),0,style)
            for group in groups:
                self.assertTrue(3<=len(group)<=6)
                self.assertTrue(all(n["instrument"]=="acoustic" for _,n in group))
                self.assertLessEqual(group[-1][1]["beat"]-group[0][1]["beat"],.18)

    def test_single_notes_are_not_misclassified_as_strums(self):
        notes=[{"instrument":"acoustic","pitch":60,"beat":.1},
               {"instrument":"electric","pitch":64,"beat":.1},
               {"instrument":"acoustic","pitch":62,"beat":2.1}]
        self.assertEqual(strum_groups(notes),[])

    def test_missing_actual_sample_assets_fail_instead_of_guessing(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises((FileNotFoundError,ValueError)):
                audit_score(make("silver"),Path(folder))


if __name__=="__main__":unittest.main()
