"""Pure score-to-score performance gestures; independent of samples and mixing.

The score is portable JSON. This module deliberately changes an existing score,
not note synthesis. Melody breathing, bass/kick dialogue and phrase energy can be
replaced without touching sound design. Deterministic for a given score.
"""
from __future__ import annotations
from copy import deepcopy
from math import sin, pi

PROFILES = {
    'indie': {'description':'Organic indie-pop pocket: guitar forward and relaxed backbeat',
              'start_bar':24, 'bars':12, 'bpm':114, 'bus_gains':{'guitar':1.19,'keys':.83,'bass':.82,'drums':.90,'lead':.94}, 'stereo_width':1.55},
    'electro': {'description':'Bright electronic-pop: locked kick/bass and bouncing hook',
                'start_bar':32, 'bars':12, 'bpm':118, 'bus_gains':{'guitar':.74,'keys':1.11,'bass':.96,'drums':1.05,'lead':1.12}, 'stereo_width':1.90},
    'hybrid': {'description':'Spacious hybrid pop: restrained bridge into a large refrain',
               'start_bar':72, 'bars':12, 'bpm':112, 'bus_gains':{'guitar':1.05,'keys':1.10,'bass':.83,'drums':.92,'lead':1.02}, 'stereo_width':1.80},
}


def make_excerpt(score: dict, profile: str) -> dict:
    """Extract and arrange an original score as a stand-alone 12-bar demo."""
    if profile not in PROFILES:
        raise ValueError(f'Unknown profile: {profile}')
    p=PROFILES[profile]
    result=deepcopy(score)
    start=p['start_bar']*4
    end=(p['start_bar']+p['bars'])*4
    result['stem']=f'Music_Studio_Example_{profile.title()}'
    result['title']=f'Music Studio - {profile.title()} Demo'
    result['bpm']=p['bpm']
    result['bars']=p['bars']
    result['duration_seconds']=p['bars']*4*60/p['bpm']+3
    result['mix']={'stereo_width':p['stereo_width'],'bus_gains':p['bus_gains']}
    result['notes']=[dict(n,beat=round(n['beat']-start,5)) for n in score['notes'] if start<=n['beat']<end]
    result['drums']=[dict(h,beat=round(h['beat']-start,5)) for h in score['drums'] if start<=h['beat']<end]
    result['sections']=[{'name':s['name'],'start':max(0,s['start']-p['start_bar']),
                         'end':min(p['bars'],s['end']-p['start_bar'])}
                        for s in score['sections'] if s['end']>p['start_bar'] and s['start']<p['start_bar']+p['bars']]
    result['chords']=[dict(c,bar=c['bar']-p['start_bar']) for c in score['chords'] if p['start_bar']<=c['bar']<p['start_bar']+p['bars']]
    result['notes']=perform_lead(result['notes'],result['bars'],profile)
    result['notes']=coordinate_bass(result['notes'],result['drums'],profile)
    result['drums']=perform_drums(result['drums'],result['bars'],profile)
    result['profile']=profile
    result['description']=p['description']
    return result


def perform_lead(notes: list[dict], bars: int, profile: str) -> list[dict]:
    """Phrase arcs, meaningful breath gaps and occasional longer cadence notes."""
    lead=[n for n in notes if n['part']=='lead']
    for bar in range(bars):
        phrase=sorted([n for n in lead if int(n['beat']//4)==bar],key=lambda n:n['beat'])
        if not phrase:continue
        # Intentional half-bar breath after four-bar phrases when possible.
        if bar in (3,7) and len(phrase)>=4:
            notes.remove(phrase[-2]);phrase.remove(phrase[-2])
        for i,n in enumerate(phrase):
            pos=(n['beat']%4)/4
            arc=.85+.15*sin(pi*min(1,max(0,pos)))
            n['velocity']=round(min(1.03,n['velocity']*arc*(.94 if profile=='indie' else 1.04 if profile=='electro' else .98)),4)
            if i==len(phrase)-1 and bar%4==3:
                # Close a phrase with a held answer, not more machine-gun notes.
                n['duration']=round(min(2.10,max(.84,n['duration']*1.75)),4)
            if profile=='indie' and i%2==1:
                n['beat']=round(n['beat']+.025,5)
            if profile=='hybrid' and i==0 and bar<8:
                n['duration']=round(min(1.5,n['duration']*1.25),4)
    return sorted(notes,key=lambda n:(n['beat'],n['part'],n['pitch']))


def coordinate_bass(notes: list[dict], drums: list[dict], profile: str) -> list[dict]:
    """Lock bass fundamentals near the kick; preserve purposeful offbeat notes."""
    kicks=[h['beat'] for h in drums if h['kind']=='kick']
    for n in notes:
        if n['part']!='bass':continue
        if kicks:
            nearest=min(kicks,key=lambda b:abs(b-n['beat']))
            if abs(nearest-n['beat'])<.13:
                n['beat']=round(nearest+.012,5)
                n['velocity']=round(min(1.05,n['velocity']*1.04),4)
        if profile=='indie' and n['beat']%4>3.7:
            n['velocity']=round(n['velocity']*.83,4)
    return sorted(notes,key=lambda n:(n['beat'],n['part'],n['pitch']))


def perform_drums(drums: list[dict], bars: int, profile: str) -> list[dict]:
    """Stable kick downbeat, late indie snares, restrained hybrid pickup fills."""
    result=[]
    for i,h in enumerate(drums):
        n=dict(h)
        if profile=='indie' and n['kind'] in ('snare','clap'):
            n['beat']=round(n['beat']+.028,5)
        if profile=='electro' and n['kind']=='kick':
            n['velocity']=round(min(1,n['velocity']*1.1),4)
        if profile=='hybrid' and n['beat']<6*4 and n['kind'] in ('hat','open_hat'):
            n['velocity']=round(n['velocity']*.67,4)
        if n['beat']<bars*4:result.append(n)
    return sorted(result,key=lambda x:x['beat'])
