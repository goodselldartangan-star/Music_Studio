"""CLI façade. Deliberately thin to keep the internal modules easy to replace."""
import argparse,json,subprocess
from pathlib import Path
from studio3 import Settings,create_score
from studio3.midi import write_midi
from studio3.mix import mix_score
from studio3.development import develop_score
from studio3.review import audit_score
from studio3.composition import CHORDS


def main():
    p=argparse.ArgumentParser(description='Offline original song renderer: no external AI or audio services')
    p.add_argument('--out',type=Path,default=Path('output'))
    p.add_argument('--preview-bars',type=int)
    p.add_argument('--bpm',type=int,default=118)
    p.add_argument('--transpose',type=int,default=0)
    p.add_argument('--seed',type=int,default=261111)
    p.add_argument('--score-only',action='store_true')
    p.add_argument('--no-mp3',action='store_true')
    p.add_argument('--no-development', action='store_true', help='Render baseline v3 score for A/B testing')
    p.add_argument('--stereo-width',type=float,default=1.95)
    args=p.parse_args()
    score=create_score(Settings(args.bpm,args.transpose,args.seed,args.preview_bars))
    if not args.no_development:
        score=develop_score(score)
    score['mix']={'stereo_width':args.stereo_width}
    if not .75<=args.stereo_width<=3.10:
        p.error('--stereo-width must be between 0.75 and 3.10')
    review=audit_score(score,CHORDS, strict=not args.no_development)
    args.out.mkdir(parents=True,exist_ok=True)
    stem=score['stem']
    (args.out/(stem+'.score.json')).write_text(json.dumps(score,indent=2))
    (args.out/'composition_review.json').write_text(json.dumps(review,indent=2))
    write_midi(score,args.out/(stem+'.mid'))
    result={'title':score['title'],'development':not args.no_development, 'score_warnings':review['warnings'], 'seconds':score['duration_seconds'],
            'notes':len(score['notes']),'drums':len(score['drums'])}
    if not args.score_only:
        result.update(mix_score(score,args.out))
        if not args.no_mp3:
            target=args.out/(stem+'.mp3')
            subprocess.run(['ffmpeg','-hide_banner','-v','error','-nostdin','-y',
                            '-i',result['wav'],'-codec:a','libmp3lame','-b:a','320k',
                            '-metadata',f"title={score['title']}",'-metadata','artist=Music Studio',str(target)],check=True)
            result['mp3']=str(target)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
