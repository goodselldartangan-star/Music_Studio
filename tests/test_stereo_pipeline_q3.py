"""Q3: integration fixtures preserve old mono playback and add separate stereo."""
import hashlib
import tempfile
import unittest
from pathlib import Path

import numpy as np
import soundfile as sf

from studio3.spec import SR
from studio7.render import _sample_meta, instrument_stems
from studio7.samples import Collection


def recording():
    t=np.arange(48000,dtype=np.float32)/48000
    left=.17*np.sin(2*np.pi*261.63*t)*np.exp(-2*t)
    right=.84*left+.013*np.sin(2*np.pi*523.25*t)*np.exp(-2*t)
    return np.column_stack([left,right])


class StereoIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name)
        self.ogg=root/'oggs'
        self.wav=root/'wavs'
        for base in (self.ogg,self.wav):
            (base/'meta-piano').mkdir(parents=True)
            (base/'meta-nylon-guitar').mkdir(parents=True)
            (base/'meta-steel-guitar').mkdir(parents=True)
        audio=recording()
        for library,filename in (
            ('meta-piano','INSPiano_Vel01_C4_01'),
            ('meta-nylon-guitar','INSGuitarNylon_StringA_Vel01Finger_E2_01'),
            ('meta-steel-guitar','INSGuitarSteel_StringLowE_Vel01_E2_01')
        ):
            sf.write(self.wav/library/(filename+'.wav'),audio,48000,subtype='PCM_24')
            sf.write(self.ogg/library/(filename+'.ogg'),audio.mean(axis=1),48000,
                     format='OGG',subtype='VORBIS')

    def test_piano_dry_source_is_stereo_only_in_opt_in_path(self):
        score={'style':'after','bars':16,'duration':4.,'bpm':120,
               'notes':[dict(instrument='piano',pitch=60,beat=.15,length=1.5,velocity=65),
                        dict(instrument='piano',pitch=60,beat=.55,length=.2,velocity=70)]}
        src=self.wav/'meta-piano'/'INSPiano_Vel01_C4_01.wav'
        original_hash=hashlib.sha256(src.read_bytes()).hexdigest()
        old=_sample_meta(score,'piano',self.ogg)
        new=_sample_meta(score,'piano',self.wav,stereo_wav=True)
        self.assertEqual(new.shape,old.shape)
        self.assertEqual(old.shape,(round(4*SR),2))
        self.assertLess(float(np.max(abs(old[:,0]-old[:,1]))),1e-8)
        self.assertGreater(float(np.max(abs(new[:,0]-new[:,1]))),.0001)
        self.assertTrue(np.isfinite(new).all())
        self.assertGreater(float(np.corrcoef(old.mean(axis=1),new.mean(axis=1))[0,1]),.95)
        self.assertEqual(hashlib.sha256(src.read_bytes()).hexdigest(),original_hash)
        np.testing.assert_array_equal(old,_sample_meta(score,'piano',self.ogg))

    def test_nylon_same_take_selection_and_release_with_stereo_sources(self):
        score={'style':'silver','bars':16,'duration':3.,'bpm':110,
               'notes':[dict(instrument='acoustic',pitch=40,beat=.1,length=1.5,velocity=75),
                        dict(instrument='acoustic',pitch=40,beat=.5,length=.23,velocity=70)]}
        bank=Collection(self.wav,'meta-nylon-guitar')
        selected=bank.select_region(40,75,14)
        self.assertEqual(selected[1],40)
        old=_sample_meta(score,'acoustic',self.ogg)
        stereo=_sample_meta(score,'acoustic',self.wav,stereo_wav=True)
        self.assertEqual(stereo.shape,old.shape)
        self.assertGreater(float(np.max(abs(stereo[:,0]-stereo[:,1]))),.0001)
        self.assertGreater(float(np.max(abs(stereo[round(.55*60/110*SR):]))),.00001)

    def test_piano_only_stereo_keeps_original_acoustic_ogg_exact(self):
        # No guitar WAV library is required for the optional piano-only path.
        for path in (self.wav/'meta-steel-guitar').glob('*.wav'):
            path.unlink()
        score={'style':'harbor','bars':16,'duration':3.,'bpm':120,'drums':[],
               'notes':[dict(instrument='acoustic',pitch=40,beat=.1,length=.9,velocity=75),
                        dict(instrument='piano',pitch=60,beat=.3,length=1.1,velocity=70)]}
        baseline=instrument_stems(score,assets=self.ogg)
        changed=instrument_stems(score,assets=self.ogg,wav_source_root=self.wav,wav_parts='piano')
        np.testing.assert_array_equal(baseline['acoustic'],changed['acoustic'])
        self.assertGreater(float(np.max(abs(changed['piano'][:,0]-changed['piano'][:,1]))),.0001)
        self.assertLess(float(np.max(abs(baseline['piano'][:,0]-baseline['piano'][:,1]))),1e-8)
        with self.assertRaises(ValueError):
            instrument_stems(score,assets=self.ogg,wav_parts='piano')

    def test_wav_source_cannot_be_silently_used_with_gm(self):
        score={'style':'after','bars':16,'duration':1.,'bpm':120,'notes':[],'drums':[]}
        with self.assertRaisesRegex(ValueError,'WAV source root requires'):
            instrument_stems(score,gm=Path('fake.sf2'),wav_source_root=self.wav)


if __name__=='__main__':unittest.main()
