"""Q3 WAV installation never overwrites and verifies channels and identities."""
import tempfile,unittest,io
from pathlib import Path
from zipfile import ZipFile
import numpy as np,soundfile as sf
from tools.install_wav_q3 import install_archive


class InstallTests(unittest.TestCase):
    def test_reject_mono_source_and_leave_no_partial_install(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);file=p/'trial.zip';dst=p/'assets'
            raw=io.BytesIO();sf.write(raw,np.zeros(4800,dtype=np.float32),48000,format='WAV',subtype='PCM_24')
            with ZipFile(file,'w') as z:z.writestr('INSPiano_Vel01_C4_01.wav',raw.getvalue())
            with self.assertRaisesRegex(ValueError,'24-bit 48k stereo'):
                install_archive('meta-piano',file,dst,strict=False)
            self.assertFalse((dst/'meta-piano').exists())

    def test_install_stereo_source_once_without_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);file=p/'trial.zip';dst=p/'assets'
            raw=io.BytesIO();sf.write(raw,np.zeros((4800,2),dtype=np.float32),48000,format='WAV',subtype='PCM_24')
            with ZipFile(file,'w') as z:z.writestr('INSPiano_Vel01_C4_01.wav',raw.getvalue())
            report=install_archive('meta-piano',file,dst,strict=False)
            self.assertEqual(report['sample_count'],1)
            self.assertEqual(sf.info(dst/'meta-piano'/'INSPiano_Vel01_C4_01.wav').channels,2)
            with self.assertRaises(FileExistsError):install_archive('meta-piano',file,dst,strict=False)


if __name__=='__main__':unittest.main()
