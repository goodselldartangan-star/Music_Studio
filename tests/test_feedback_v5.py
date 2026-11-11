"""Contract tests for feedback profiles, recorded drums and independent performance."""
import hashlib
from pathlib import Path
import tempfile
import unittest
import numpy as np
import soundfile as sf
from studio3 import create_score,Settings
from studio3.development import develop_score
from studio3.performance import PROFILES, make_excerpt
from studio3.sample_bank import SampleBank
from studio3.mix import mix_score
from tools.install_cc0_drums import FILES, git_blob_sha,install


class FeedbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.score=develop_score(create_score(Settings()))

    def test_three_examples_distinct(self):
        snippets=[make_excerpt(self.score,p) for p in PROFILES]
        self.assertEqual(len(snippets),3)
        self.assertEqual(len(set(x['stem'] for x in snippets)),3)
        self.assertEqual(len(set(x['bpm'] for x in snippets)),3)
        for x in snippets:
            self.assertEqual(x['bars'],12)
            self.assertTrue(x['notes'] and x['drums'])
            self.assertTrue(all(0<=n['beat']<48 for n in x['notes']))
            self.assertTrue(all(0<=n['beat']<48 for n in x['drums']))
            self.assertTrue(all(0<=s['start']<s['end']<=12 for s in x['sections']))

    def test_phrase_last_note_sustained(self):
        score=make_excerpt(self.score,'electro')
        lengths=[n['duration'] for n in score['notes'] if n['part']=='lead' and 12<=n['beat']<16]
        self.assertGreater(max(lengths),.8)

    def test_bass_kick_interaction(self):
        s=make_excerpt(self.score,'electro')
        kicks=[x['beat'] for x in s['drums'] if x['kind']=='kick']
        aligned=[n for n in s['notes'] if n['part']=='bass' and any(abs(k-n['beat'])<.015 for k in kicks)]
        self.assertGreater(len(aligned),8)

    def test_unknown_profile(self):
        with self.assertRaises(ValueError):make_excerpt(self.score,'not-a-profile')

    def test_installer_verification_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            def wrong(_):return b'RIFFxxxxWAVE'+b'x'*100
            with self.assertRaises(ValueError):install(Path(d),wrong)

    def test_drum_sample_playback_and_ghost(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for kind in ('kick','snare','hat','open_hat'):
                p=root/'drums'/kind/(kind+'.wav');p.parent.mkdir(parents=True,exist_ok=True)
                sr=44100;t=np.arange(round(.12*sr))/sr
                y=(.25*np.sin(2*np.pi*(80 if kind=='kick' else 500)*t)*np.exp(-t*24)).astype(np.float32)
                sf.write(p,y,sr)
            bank=SampleBank(root)
            self.assertTrue(bank.has('ghost'))
            self.assertTrue(bank.has('kick'))
            a=bank.render_drum('snare',.5,123)
            b=bank.render_drum('ghost',.5,123)
            self.assertTrue(np.isfinite(a).all())
            self.assertLess(np.max(np.abs(b)),np.max(np.abs(a)))

    def test_required_drum_pack(self):
        with tempfile.TemporaryDirectory() as tmp:
            s=make_excerpt(self.score,'indie')
            with self.assertRaises(FileNotFoundError):mix_score(s,Path(tmp),require_drums=True)

if __name__=='__main__':unittest.main()

class InstallerSmokeTests(unittest.TestCase):
    def test_success_with_verifiable_fixture(self):
        import io
        from unittest.mock import patch
        import tools.install_cc0_drums as module
        stream=io.BytesIO()
        sf.write(stream,np.array([0,.1,-.1,0],dtype=np.float32),44100,format='WAV',subtype='PCM_16')
        data=stream.getvalue()
        expected=module.git_blob_sha(data)
        with tempfile.TemporaryDirectory() as root,patch.object(module,'FILES',[('kick','test/kick.wav',expected)]):
            result=module.install(Path(root),lambda _:data)
            self.assertEqual(result['files'][0]['git_blob_sha1'],expected)
            self.assertTrue((Path(root)/'drums/kick/test-kick.wav').is_file())
            self.assertTrue(SampleBank(root).has('kick'))
