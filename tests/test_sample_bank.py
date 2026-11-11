"""Independent tests for recorded-note selection, articulation and archive safety.

Fixtures are generated locally; they are *not* represented as real recordings.
"""
import math
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile
import numpy as np
import soundfile as sf
from studio3.spec import Note, SR, Settings
from studio3.sample_bank import SampleBank, midi_from_name, _at_pitch
from tools.install_cc0 import install_pack


class BankTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for inst, name in [('meta-steel-guitar', 'INSGuitarSteel_StringE_Vel02Pick_G3_01.wav'),
                           ('meta-piano', 'INSPiano_Vel02_C4_01.wav')]:
            path = self.root / inst
            path.mkdir()
            sr = 48000
            t = np.arange(int(sr * .5)) / sr
            signal = (.4 * np.sin(2 * np.pi * (196 if inst == 'meta-steel-guitar' else 261.626) * t)
                      * np.exp(-t*3)).astype(np.float32)
            sf.write(path/name, signal, sr)

    def tearDown(self): self.tmp.cleanup()

    def test_pitch_parser(self):
        self.assertEqual(midi_from_name('G3'), 55)
        self.assertEqual(midi_from_name('Fs4'), 66)
        self.assertEqual(midi_from_name('C4'), 60)

    def test_inventory_and_selection(self):
        bank=SampleBank(self.root)
        self.assertEqual(bank.inventory()['pluck'], 1)
        self.assertEqual(bank.inventory()['keys'], 1)
        self.assertTrue(bank.has('pluck'))
        self.assertFalse(bank.has('bass'))

    def test_real_note_interface(self):
        bank=SampleBank(self.root)
        for part,pitch in [('pluck',55), ('keys',60)]:
            n=Note(part,1,.4,pitch,.65)
            x=bank.render_note(n,120,123)
            self.assertEqual(len(x),round((.4*60/120+(.11 if part=='pluck' else .17))*SR))
            self.assertTrue(np.isfinite(x).all())
            self.assertGreater(np.max(np.abs(x)),.001)
            self.assertTrue(np.array_equal(x,bank.render_note(n,120,123)))

    def test_velocity_is_respected(self):
        bank=SampleBank(self.root)
        a=bank.render_note(Note('pluck',0,.5,55,.25),120,5)
        b=bank.render_note(Note('pluck',0,.5,55,.75),120,5)
        self.assertGreater(np.max(np.abs(b)),2*np.max(np.abs(a)))

    def test_transposition_and_bad_range(self):
        bank=SampleBank(self.root)
        x=bank.render_note(Note('pluck',0,.3,58,.5),120,7)
        self.assertTrue(np.isfinite(x).all())
        with self.assertRaises(ValueError):
            bank.render_note(Note('pluck',0,.3,80,.5),120,7)

    def test_wrong_files_cannot_pass_as_installed(self):
        empty=self.root/'empty';empty.mkdir()
        self.assertFalse(SampleBank(empty).has('pluck'))

    def test_valid_zip_install_and_path_safety(self):
        archive=self.root/'src.zip'
        with ZipFile(archive,'w') as z:
            z.write(self.root/'meta-piano'/'INSPiano_Vel02_C4_01.wav',
                    'meta-piano/ogg/INSPiano_Vel02_C4_01.ogg')
        output=self.root/'installed'
        result=install_pack('meta-piano',archive,output)
        self.assertEqual(result['files'],1)
        self.assertTrue((output/'meta-piano'/'INSPiano_Vel02_C4_01.ogg').exists())
        attack=self.root/'bad.zip'
        with ZipFile(attack,'w') as z:z.writestr('../bad.ogg',b'not a file')
        with self.assertRaises(ValueError):install_pack('meta-piano',attack,output)


if __name__=='__main__':unittest.main()
