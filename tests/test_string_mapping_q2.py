"""Q2: source-zone chord assignment without note-offs or musical edits."""
import unittest
from copy import deepcopy
from pathlib import Path
from studio7.string_mapping import plan_guitar_samples,shape_harbor_bm_guitar
from studio7.score import make,validate


def source(zone,layer,pitch,name="C4"):
    return (Path(f"INSGuitarSteel_String{zone}_Vel0{layer}_{name}_01.wav"),pitch,layer)


class StringMappingTests(unittest.TestCase):
    def setUp(self):
        self.notes=[
            dict(instrument="acoustic",pitch=p,beat=.12+i*.04,length=1.1,
                 velocity=80)
            for i,p in enumerate((50,54,57,62))
        ]
        self.regions=[
            source("A",2,50,"D3"),source("D",2,50,"D3"),
            source("A",2,54,"Fs3"),source("D",2,54,"Fs3"),
            source("D",2,57,"A3"),source("G",2,57,"A3"),
            source("G",2,62,"D4"),source("B",2,62,"D4"),
        ]

    def test_four_note_strum_uses_four_increasing_distinct_strings(self):
        before=deepcopy(self.notes)
        assigned,report=plan_guitar_samples(self.notes,self.regions,seed_base=15)
        self.assertEqual(self.notes,before)
        self.assertEqual(report["strums"],1)
        self.assertEqual(report["mapped_distinct_strums"],1)
        self.assertEqual(report["remaining_intra_strum_string_conflicts"],0)
        self.assertEqual(report["assignments"][0]["source_strings"],["A","D","G","B"])
        self.assertEqual([x[1] for x in assigned],[50,54,57,62])

    def test_identical_samples_after_only_strum_timing_is_changed(self):
        before,_=plan_guitar_samples(self.notes,self.regions,seed_base=78)
        modified=deepcopy(self.notes)
        for j,note in enumerate(modified):
            note["beat"]+=.007*j
        after,_=plan_guitar_samples(modified,self.regions,seed_base=78)
        self.assertEqual(before,after)

    def test_upstroke_preserves_reverse_picking_order(self):
        reversed_notes=list(reversed(self.notes))
        for i,note in enumerate(reversed_notes):note=dict(note,beat=1.2+i*.027);reversed_notes[i]=note
        regions,stats=plan_guitar_samples(reversed_notes,self.regions,seed_base=40)
        self.assertEqual(stats["remaining_intra_strum_string_conflicts"],0)
        self.assertEqual(stats["assignments"][0]["source_strings"],["B","G","D","A"])
        self.assertEqual([r[1] for r in regions],[62,57,54,50])

    def test_retriggered_pitch_keeps_take_when_shifted_but_not_truncated(self):
        notes=[dict(instrument="acoustic",pitch=62,beat=b,length=l,velocity=70)
               for b,l in ((.1,2.5),(.64,.2))]
        regions=[source("G",2,62,"D4"),source("B",2,62,"D4")]
        chosen,report=plan_guitar_samples(notes,regions,seed_base=4)
        shifted=deepcopy(notes)
        shifted[1]["beat"]+=.035
        shifted[1]["length"]+=.4
        again,_=plan_guitar_samples(shifted,regions,seed_base=4)
        self.assertEqual(chosen,again)
        self.assertEqual([n["length"] for n in notes],[2.5,.2])
        self.assertEqual(report["strums"],0)

    def test_impossible_unique_strings_fall_back_without_losing_notes(self):
        limited=[source("A",2,p,n) for p,n in ((50,"D3"),(54,"Fs3"),(57,"A3"),(62,"D4"))]
        picked,report=plan_guitar_samples(self.notes,limited)
        self.assertEqual(len(picked),4)
        self.assertEqual(report["mapped_distinct_strums"],0)
        self.assertEqual(report["unmapped_strums"],1)
        self.assertEqual(report["remaining_intra_strum_string_conflicts"],3)

    def test_targeted_b_minor_revoicing_keeps_harmony_and_non_guitar_parts(self):
        source=make("harbor")
        frozen=deepcopy(source)
        shaped,report=shape_harbor_bm_guitar(source)
        self.assertEqual(source,frozen)
        self.assertEqual(report["chords_revoiced"],8)
        self.assertEqual(report["notes_repitched"],24)
        self.assertEqual(len(shaped["notes"]),len(source["notes"]))
        self.assertEqual(shaped["drums"],source["drums"])
        self.assertEqual(shaped["chords"],source["chords"])
        self.assertTrue(validate(shaped)["validated"])
        for old,new in zip(source["notes"],shaped["notes"]):
            self.assertEqual((old["instrument"],old["beat"],old["length"],old["velocity"]),
                             (new["instrument"],new["beat"],new["length"],new["velocity"]))
            if old["instrument"]!="acoustic":
                self.assertEqual(old,new)
        first=[n for n in shaped["notes"] if n["instrument"]=="acoustic"
               and 8<=n["beat"]<8.3]
        self.assertEqual(sorted(n["pitch"] for n in first),[47,54,59,62])
        self.assertEqual(sorted(n["pitch"]%12 for n in first),[2,6,11,11])

    def test_unrelated_style_never_gets_guitar_octave_shift(self):
        source=make("silver")
        changed,report=shape_harbor_bm_guitar(source)
        self.assertEqual(source,changed)
        self.assertEqual(report["chords_revoiced"],0)

    def test_missing_regions_and_bad_velocity_are_rejected(self):
        with self.assertRaises(FileNotFoundError):
            plan_guitar_samples(self.notes,[])
        bad=deepcopy(self.notes)
        bad[0]["velocity"]=0
        with self.assertRaises(ValueError):
            plan_guitar_samples(bad,self.regions)

if __name__=="__main__":unittest.main()
