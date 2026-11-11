"""P1: changing a note duration must not silently select a different recording."""
import tempfile
import unittest
from pathlib import Path
import numpy as np
import soundfile as sf
from studio7.samples import Collection
from studio6.soundfonts import SR


class TakeIdentity(unittest.TestCase):
    def test_round_robin_does_not_depend_on_note_length(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/'meta-nylon-guitar'
            folder.mkdir()
            t=np.arange(SR, dtype=np.float32)/SR
            # Two distinctive recorded 'takes' at the same note and velocity layer.
            for i,phase in enumerate((0,.8),start=1):
                y=(.22*np.sin(2*np.pi*82.4069*t+phase)*np.exp(-t)).astype(np.float32)
                sf.write(folder/f'INSGuitarNylon_StringLowE_Vel01Finger_E2_{i:02d}.wav',y,SR)
            bank=Collection(Path(tmp),'meta-nylon-guitar')
            for seed in range(20):
                short=bank.render(40,42,.32,112,seed)
                long=bank.render(40,42,.9,112,seed)
                # Compare identical source attacks, not their deliberately different note releases.
                np.testing.assert_allclose(short[:round(.1*SR)],long[:round(.1*SR)],atol=1e-7)


if __name__=='__main__':unittest.main()
