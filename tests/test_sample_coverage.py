"""P1 coverage audit: missing packs must fail; exact-key fixtures must pass."""
import tempfile
import unittest
from pathlib import Path
import numpy as np
import soundfile as sf
from tools.audit_sample_coverage import audit_assets
from studio7.score import SONGS, make


def note_label(pitch):
    names=['C','Cs','D','Ds','E','F','Fs','G','Gs','A','As','B']
    return names[pitch%12]+str(pitch//12-1)


class SampleCoverage(unittest.TestCase):
    def test_empty_asset_root_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises((FileNotFoundError,AssertionError)):
                audit_assets(Path(tmp))

    def test_report_covers_actual_score_pitches_when_available(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            sources={}
            for style in SONGS:
                for n in make(style)['notes']:
                    part=n['instrument']
                    if part not in ('acoustic','piano'):continue
                    source='meta-nylon-guitar' if style=='silver' and part=='acoustic' else (
                        'meta-steel-guitar' if part=='acoustic' else 'meta-piano')
                    sources.setdefault(source,set()).add(n['pitch'])
            audio=np.zeros(round(.20*44100),dtype=np.float32)
            for source,pitches in sources.items():
                folder=root/source
                folder.mkdir()
                for pitch in pitches:
                    for layer in range(1,5):
                        path=folder/f'Instrument_Vel0{layer}Finger_{note_label(pitch)}_01.wav'
                        sf.write(path,audio,44100)
            report=audit_assets(root)
            self.assertEqual(set(report['scores']),set(SONGS))
            self.assertTrue(all(v['max_transpose_semitones']==0 for v in report['scores'].values()))
            self.assertTrue(all(v['exact_pitch_hits']==v['sampled_notes'] for v in report['scores'].values()))
            self.assertGreater(report['sources']['pluck']['recordings'],1)
            self.assertEqual(len(report['velocity_probes']),3)
            self.assertTrue(all(len(set(v['layers_at_velocity_24_70_115']))==3
                                for v in report['velocity_probes'].values()))


if __name__=='__main__':unittest.main()
