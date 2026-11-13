"""Q3 WAV/OGG same-take pair tests with no external downloads."""
import io
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
import numpy as np
import soundfile as sf
from tools.audit_wav_ogg_q3 import compare_archives, _match_similarity


def source_sr(sr=48000, seconds=1.8):
    t=np.arange(round(sr*seconds),dtype=np.float64)/sr
    gate=(1-np.exp(-t*250.)) * np.exp(-t*1.7)
    left=.17*np.sin(2*np.pi*392*t)*gate + .03*np.sin(2*np.pi*780*t)*gate
    right=.15*np.sin(2*np.pi*392*t + .14)*gate + .02*np.sin(2*np.pi*780*t+.3)*gate
    return np.stack([left,right],axis=1).astype('float32')


def audio_bytes(a,subtype,format):
    f=io.BytesIO()
    sf.write(f,a,48000,format=format,subtype=subtype)
    return f.getvalue()


class PairedSources(unittest.TestCase):
    def test_exact_basename_pairs_and_stereo_master(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            wav=root/'piano-wav.zip';ogg=root/'piano-ogg.zip'
            s=source_sr()
            with ZipFile(wav,'w') as a,ZipFile(ogg,'w') as b:
                for index in range(5):
                    stem=f'INSPiano_Vel0{index%3+1}_Gs5_{index+1:02}'
                    w=s*(1.-index*.08)
                    a.writestr(f'wrapped/{stem}.wav',audio_bytes(w,'PCM_24','WAV'))
                    b.writestr(f'wrapped/{stem}.ogg',audio_bytes(w.mean(axis=1),'VORBIS','OGG'))
            report=compare_archives(ogg,wav,max_pairs=4)
            self.assertEqual(report['ogg_file_count'],5)
            self.assertEqual(report['wav_file_count'],5)
            self.assertEqual(report['same_filename_pairs'],5)
            self.assertEqual(report['checked_pair_count'],4)
            self.assertEqual(report['candidate_same_take_count'],4)
            self.assertEqual(report['wav_channel_counts'],{'2':4})
            self.assertEqual(report['ogg_channel_counts'],{'1':4})
            self.assertTrue(all(x['wav']['side_to_mid_rms']>0 for x in report['tested_pairs']))

    def test_unmatched_notes_are_not_mistaken_for_same_takes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);wav=root/'wav.zip';ogg=root/'ogg.zip'
            s=source_sr()
            with ZipFile(wav,'w') as a,ZipFile(ogg,'w') as b:
                for index in range(3):
                    a.writestr(f'note{index}.wav',audio_bytes(s,'PCM_24','WAV'))
                    b.writestr(f'different{index}.ogg',audio_bytes(s.mean(axis=1),'VORBIS','OGG'))
            with self.assertRaisesRegex(ValueError,'No exact file-basename matches'):
                compare_archives(ogg,wav)

    def test_different_source_waveforms_are_not_verified(self):
        sr=48000;t=np.arange(sr)/sr
        a=np.sin(2*np.pi*440*t).astype('float32')
        b=np.sin(2*np.pi*550*t).astype('float32')
        self.assertLess(_match_similarity(a[:,None],b[:,None],sr)['correlation'],.2)

    def test_pair_limit_is_bounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp)/'a.zip';b=Path(tmp)/'b.zip'
            with ZipFile(a,'w') as z:z.writestr('x.ogg',b'1')
            with ZipFile(b,'w') as z:z.writestr('x.wav',b'1')
            with self.assertRaises(ValueError):compare_archives(a,b,max_pairs=90)


if __name__=='__main__':unittest.main()
