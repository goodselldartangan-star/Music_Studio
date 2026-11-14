"""Q4: actual stereo/mono sample-selection interfaces behave together.

Small synthetic 24-bit stereo WAV/mono OGG fixture. The full publisher
recording inventory is checked by tools.verify_string_stereo_q4 in CI.
"""
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path

import numpy as np
import soundfile as sf

from studio3.sample_bank import SampleBank
from studio7.samples import Collection
from studio7.render import _sample_meta
from studio7.string_mapping import plan_guitar_samples
from tools.verify_string_stereo_q4 import _identity


class MatchedStringStereoTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root=Path(temp.name)
        self.ogg=root/'ogg'
        self.wav=root/'wav'
        for library in ('meta-steel-guitar','meta-nylon-guitar','meta-piano'):
            (self.ogg/library).mkdir(parents=True)
            (self.wav/library).mkdir(parents=True)
        sr=48000
        t=np.arange(sr,dtype=np.float32)/sr
        left=(.15*np.sin(2*np.pi*196*t)*np.exp(-1.3*t)).astype(np.float32)
        right=(.86*left+.02*np.sin(2*np.pi*327*t)*np.exp(-1.5*t)).astype(np.float32)
        stereo=np.stack([left,right],axis=1)
        sources=(('meta-steel-guitar','INSGuitarSteel_'),
                 ('meta-nylon-guitar','INSGuitarNylon_'))
        for library,prefix in sources:
            for zone,note in (('LowE','E2'),('A','A2'),('D','D3')):
                name=f'{prefix}String{zone}_Vel02_{note}_01'
                sf.write(self.wav/library/(name+'.wav'),stereo,sr,subtype='PCM_24')
                sf.write(self.ogg/library/(name+'.ogg'),stereo.mean(axis=1),sr,
                         format='OGG',subtype='VORBIS')
        sf.write(self.wav/'meta-piano'/'INSPiano_Vel02_C4_01.wav',
                 stereo,sr,subtype='PCM_24')
        sf.write(self.ogg/'meta-piano'/'INSPiano_Vel02_C4_01.ogg',
                 stereo.mean(axis=1),sr,format='OGG',subtype='VORBIS')

    @staticmethod
    def _notes():
        notes=[dict(instrument='acoustic',pitch=p,beat=b,length=1.5,velocity=78)
               for p,b in ((40,.1),(45,.13),(50,.16))]
        notes.append(dict(instrument='acoustic',pitch=40,beat=.75,length=.18,velocity=72))
        return notes

    def _score(self,style,notes):
        return {'style':style,'bars':16,'duration':3.,'bpm':120,
                'notes':notes,'drums':[]}

    def test_real_stereo_path_uses_same_physically_distinct_takes_as_ogg(self):
        for style,library in (('harbor','meta-steel-guitar'),
                              ('silver','meta-nylon-guitar')):
            with self.subTest(style=style):
                regions_ogg=(SampleBank(self.ogg).regions[library] if style=='harbor'
                             else Collection(self.ogg,library).regions)
                regions_wav=(SampleBank(self.wav).regions[library] if style=='harbor'
                             else Collection(self.wav,library).regions)
                notes=self._notes()
                old,ogreport=plan_guitar_samples(notes,regions_ogg,seed_base=688)
                new,wreport=plan_guitar_samples(notes,regions_wav,seed_base=688)
                self.assertEqual([_identity(x) for x in old],
                                 [_identity(x) for x in new])
                self.assertEqual(ogreport['mapped_distinct_strums'],1)
                self.assertEqual(wreport['mapped_distinct_strums'],1)
                self.assertEqual(wreport['remaining_intra_strum_string_conflicts'],0)
                original=self._score(style,notes)
                mono=_sample_meta(original,'acoustic',self.ogg,string_aware=True)
                stereo=_sample_meta(original,'acoustic',self.wav,
                                    string_aware=True,stereo_wav=True)
                self.assertEqual(mono.shape,stereo.shape)
                self.assertLess(float(np.max(abs(mono[:,0]-mono[:,1]))),1e-7)
                self.assertGreater(float(np.max(abs(stereo[:,0]-stereo[:,1]))),.0001)
                self.assertTrue(np.isfinite(stereo).all())

    def test_second_pluck_does_not_steal_first_ring_in_stereo_mode(self):
        for style in ('harbor','silver'):
            notes=self._notes()
            whole=_sample_meta(self._score(style,notes),'acoustic',
                               self.wav,string_aware=True,stereo_wav=True)
            initial=_sample_meta(self._score(style,notes[:-1]),'acoustic',
                                 self.wav,string_aware=True,stereo_wav=True)
            new_at=round(.75*60/120*44100)
            np.testing.assert_array_equal(whole[:new_at],initial[:new_at])
            self.assertGreater(float(np.max(abs(initial[new_at:new_at+500]))),1e-6)
            self.assertGreater(float(np.max(abs(whole[new_at:new_at+500]-
                                                initial[new_at:new_at+500]))),1e-6)

    def test_unmatched_source_names_are_visible_to_take_identity_audit(self):
        a=SampleBank(self.ogg).regions['meta-steel-guitar'][0]
        b=SampleBank(self.wav).regions['meta-steel-guitar'][0]
        self.assertEqual(_identity(a),_identity(b))
        mismatched=(Path('fake_extra_take.wav'),b.midi,b.layer)
        self.assertNotEqual(_identity(a),_identity(mismatched))

    def test_guitar_string_plan_does_not_change_stereo_piano(self):
        notes=[dict(instrument='piano',pitch=60,beat=.20,length=1.1,velocity=83)]
        score=self._score('harbor',self._notes()+notes)
        piano_before=_sample_meta(score,'piano',self.wav,stereo_wav=True)
        piano_after=_sample_meta({**score,'notes':self._notes()[:3]+notes},
                                 'piano',self.wav,stereo_wav=True)
        np.testing.assert_array_equal(piano_before,piano_after)
        self.assertGreater(float(np.max(abs(piano_before[:,0]-piano_before[:,1]))),.0001)


if __name__=='__main__':
    unittest.main()
