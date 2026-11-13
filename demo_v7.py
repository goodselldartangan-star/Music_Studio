"""Render three short, original instrument arrangements, no other AI service."""
import argparse,json
from pathlib import Path
from studio7.score import SONGS
from studio7.render import render
from studio7.qa import inspect

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,default=Path('output_v7'))
    backend=p.add_mutually_exclusive_group(required=True)
    backend.add_argument('--assets',type=Path)
    backend.add_argument('--gm',type=Path)
    p.add_argument('--style',choices=list(SONGS))
    p.add_argument('--guitar-performance',action='store_true',help='P2 optional strum gestures')
    p.add_argument('--bass-performance',action='store_true',help='P2 optional bass articulation')
    p.add_argument('--piano-performance',action='store_true',help='P2 optional piano touch and rolled chords')
    p.add_argument('--rhythm-pocket',action='store_true',help='P3 optional kick/bass pocket')
    p.add_argument('--drum-dynamics',action='store_true',help='P3 optional existing-hit dynamic accents')
    p.add_argument('--register-separation',action='store_true',help='P4 optional piano/foreground octave spacing')
    p.add_argument('--melody-answer',action='store_true',help='P5 optional authored final motif cadence')
    p.add_argument('--room-predelay-ms',type=float,default=0.,help='P6 wet room predelay, 0–160 ms')
    p.add_argument('--precise-low-mono',action='store_true',help='P7 optional zero-phase low-frequency side rejection')
    p.add_argument('--transition-breath',action='store_true',help='P8 optional backing pause before returning final section')
    p.add_argument('--guitar-string-mapping',action='store_true',help='Q2 optional physically mapped recorded guitar chord strings')
    p.add_argument('--wav-source-root',type=Path,help='Q3 optional separate original stereo 24-bit WAV instrument folder')
    a=p.parse_args();results=[]
    for style in ([a.style] if a.style else SONGS):
        mp3,meta=render(style,a.out,assets=a.assets,gm=a.gm,guitar_performance=a.guitar_performance,
                        bass_performance=a.bass_performance,
                        piano_performance=a.piano_performance,
                        rhythm_pocket=a.rhythm_pocket,
                        drum_dynamics=a.drum_dynamics,
                        register_separation=a.register_separation,
                        melody_answer=a.melody_answer,
                        room_predelay_ms=a.room_predelay_ms,
                        precise_low_mono=a.precise_low_mono,
                        transition_breath=a.transition_breath,
                        guitar_string_mapping=a.guitar_string_mapping,
                        wav_source_root=a.wav_source_root)
        report=inspect(mp3)
        results.append({'metadata':meta,'audio_qa':report})
    (a.out/'verification_v7.json').write_text(json.dumps(results,indent=2))
    print(json.dumps(results,indent=2))
if __name__=='__main__':main()
