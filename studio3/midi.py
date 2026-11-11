"""MIDI interchange is independent of sound design and mixing."""
from pathlib import Path
import mido

PROGRAMS={'bass':(0,38),'pluck':(1,26),'keys':(2,4),'pad':(3,89),
          'arp':(4,81),'lead':(5,81),'counter':(6,80),'bell':(7,10)}
DRUMS={'kick':36,'snare':38,'ghost':37,'clap':39,'hat':42,'open_hat':46,
       'shaker':82,'rim':37,'tom':45,'impact':49}
TICKS=480


def write_midi(score:dict,path:Path):
    midi=mido.MidiFile(ticks_per_beat=TICKS)
    t=mido.MidiTrack();midi.tracks.append(t)
    t.append(mido.MetaMessage('track_name',name=score['title'],time=0))
    t.append(mido.MetaMessage('set_tempo',tempo=mido.bpm2tempo(score['bpm']),time=0))
    t.append(mido.MetaMessage('time_signature',numerator=4,denominator=4,time=0))
    for part,(channel,program) in PROGRAMS.items():
        tr=mido.MidiTrack();midi.tracks.append(tr)
        tr.append(mido.MetaMessage('track_name',name=part,time=0))
        tr.append(mido.Message('program_change',channel=channel,program=program,time=0))
        events=[]
        for n in score['notes']:
            if n['part']!=part:continue
            st=round(n['beat']*TICKS);en=round((n['beat']+n['duration'])*TICKS)
            vel=max(1,min(127,round(n['velocity']*110)))
            events.extend([(st,1,n['pitch'],vel),(en,0,n['pitch'],0)])
        append(tr,events,channel)
    tr=mido.MidiTrack();midi.tracks.append(tr)
    tr.append(mido.MetaMessage('track_name',name='percussion',time=0))
    events=[]
    for hit in score['drums']:
        st=round(hit['beat']*TICKS);p=DRUMS[hit['kind']]
        vel=max(1,min(127,round(hit['velocity']*110)))
        events.extend([(st,1,p,vel),(st+55,0,p,0)])
    append(tr,events,9)
    midi.save(path)


def append(track,events,channel):
    last=0
    for tick,is_on,pitch,vel in sorted(events,key=lambda item:(item[0],item[1])):
        track.append(mido.Message('note_on' if is_on else 'note_off',channel=channel,
                                  note=pitch,velocity=vel,time=tick-last));last=tick
