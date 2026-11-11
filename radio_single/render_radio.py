"""Reproducible radio-pop instrumental: score -> MIDI -> WAV -> MP3."""
import argparse,json,subprocess
from pathlib import Path
from studio3.radio_composition import compose,BPM
from studio3.midi import write_midi
from studio3.radio_mix import mix_score
from studio3.radio_quality import audit_score, check_audio

def main():
    a=argparse.ArgumentParser()
    a.add_argument('--out',type=Path,default=Path('output'))
    a.add_argument('--bpm',type=int,default=BPM)
    a.add_argument('--seed',type=int,default=113026)
    a.add_argument('--preview-bars',type=int,default=None)
    a.add_argument('--score-only',action='store_true')
    args=a.parse_args()
    score=compose(args.bpm,args.seed,args.preview_bars)
    preflight=audit_score(score)
    args.out.mkdir(parents=True,exist_ok=True)
    stem=score['stem']
    (args.out/(stem+'.score.json')).write_text(json.dumps(score,indent=2))
    (args.out/'composition_review.json').write_text(json.dumps(preflight,indent=2))
    write_midi(score,args.out/(stem+'.mid'))
    if not args.score_only:
        result=mix_score(score,args.out)
        mp3=args.out/(stem+'.mp3')
        subprocess.run(['ffmpeg','-hide_banner','-v','error','-nostdin','-y',
                        '-i',result['wav'],'-codec:a','libmp3lame','-b:a','320k',
                        '-metadata',f"title={score['title']}",'-metadata','artist=Music Studio',str(mp3)],check=True)
        report=check_audio(args.out,score,full=args.preview_bars is None)
        (args.out/'quality_report.json').write_text(json.dumps(report,indent=2))
        print(json.dumps({'mp3':str(mp3),'qa':report},indent=2))
    else: print(json.dumps(preflight,indent=2))
if __name__=='__main__':main()
