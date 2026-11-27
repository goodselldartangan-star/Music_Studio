"""Q4 physical pedal-noise routing: exact MIDI notes preserved across lanes."""
import tempfile
import unittest
from pathlib import Path

import mido

from tools.render_sfz_lanes_q4 import prepare as lanes_prepare,FIXTURE
from tools.sfz_pedal_controller_q4 import (
    prepare as pedal_prepare, write_voice_only_sfz)


def significant(path:Path):
    return [(t,msg.type,getattr(msg,"note",None),getattr(msg,"velocity",None),
             msg.channel if hasattr(msg,"channel") else None)
            for t,msg in absolute(mido.MidiFile(path).tracks[0])
            if msg.type in ("note_on","note_off")]


def absolute(track):
    time=0
    for msg in track:
        time+=msg.time
        yield time,msg


class PedalSourceRoutingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.bank=self.root/"original_bank"
        (self.bank/"Data").mkdir(parents=True)
        (self.bank/"Data"/"pedal.txt").write_text(
            "master_label=pedalAction\n<group> on_locc64=127 "
            "on_hicc64=127\n<region> sample=pedalD1.$EXT\n")
        lanes_prepare(self.root/"lanes",FIXTURE,120.,4.)

    def test_each_note_lane_keeps_original_notes_and_cc64_but_mutes_cc22(self):
        root=self.root/"lanes"
        report=pedal_prepare(root,self.bank,bpm=120.,duration_s=4.,
                             windows=[(.5,1.3)])
        self.assertEqual(report["lane_count"],2)
        self.assertEqual(report["shared_mechanism_instances"],1)
        self.assertEqual(report["cc64_movement_count"],2)
        self.assertEqual(report["original_note_count"],2)
        for n in range(2):
            old=root/f"lane_{n:02d}.mid"
            new=root/f"with_pedal_lane_{n:02d}.mid"
            self.assertEqual(significant(old),significant(new))
            cc=[(t,msg.control,msg.value) for t,msg in
                absolute(mido.MidiFile(new).tracks[0])
                if msg.type=="control_change"]
            self.assertEqual(cc,[(0,22,0),(240,64,127),(624,64,0)])
        shared=root/"shared_pedal.mid"
        cc=[(t,msg.control,msg.value) for t,msg in
            absolute(mido.MidiFile(shared).tracks[0])
            if msg.type=="control_change"]
        self.assertEqual(cc,[(0,22,64),(240,64,127),(624,64,0)])
        sfz=(root/"shared_pedal.sfz").read_text()
        self.assertIn("amplitude_oncc22=200",sfz)
        self.assertIn("pedal.txt",sfz)
        self.assertNotIn("C4v12",sfz)

    def test_derived_voice_program_cannot_trigger_physical_mechanism(self):
        source=self.bank/"Salamander Grand Piano V3.sfz"
        original=("<control>\\ndefault_path=Samples/\\n"
                  '<group> key=60\\n<region> sample=C4v12.flac\\n'
                  '<global>\\n#include "Data/pedal.txt"\\n')
        source.write_text(original)
        (self.bank/"Samples").mkdir(exist_ok=True)
        dest=self.root/"derived"/"Q4_voice_only.sfz"
        write_voice_only_sfz(source,dest,self.bank)
        self.assertEqual(source.read_text(),original)
        self.assertNotIn('#include "Data/pedal.txt"',dest.read_text())
        self.assertIn("sample=C4v12.flac",dest.read_text())
        self.assertTrue((dest.parent/"Data").is_symlink())
        self.assertTrue((dest.parent/"Samples").is_symlink())
        self.assertFalse((dest.parent/"Data").readlink().is_absolute())
        self.assertFalse((dest.parent/"Samples").readlink().is_absolute())
        write_voice_only_sfz(source,dest,self.bank)
        # The original full score is never changed, only derived presentation.
        self.assertEqual(source.read_text(),original)
        with self.assertRaisesRegex(ValueError,"exactly one"):
            write_voice_only_sfz(
                self.bank/"Data"/"pedal.txt",
                self.root/"unexpected"/"voice.sfz",self.bank)

    def test_missing_genuine_pedal_map_cannot_be_faked(self):
        (self.bank/"Data"/"pedal.txt").unlink()
        with self.assertRaises(FileNotFoundError):
            pedal_prepare(self.root/"lanes",self.bank,bpm=120.,
                          duration_s=4.,windows=[(.5,1.3)])

    def test_pedal_plan_must_share_exact_score_clock(self):
        with self.assertRaisesRegex(ValueError,"clock differ"):
            pedal_prepare(self.root/"lanes",self.bank,bpm=110.,
                          duration_s=4.,windows=[(.5,1.3)])


if __name__=="__main__":
    unittest.main()
