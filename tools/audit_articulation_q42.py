"""Q4.2 source-articulation inventory, separate from all music rendering.

Only claim source-file *labels* and SF2/SFZ zone structure, never that an
unnamed articulation is audibly absent. No AI or new instrument sounds.
"""
from __future__ import annotations
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import struct

META_NAMES={
    "steel":("meta-steel-guitar",375,125),
    "nylon":("meta-nylon-guitar",348,116),
}
STRINGS={"LowE","A","D","G","B","HighE"}
NAME=re.compile(
    r"^INSGuitar(Steel|Nylon)_String(LowE|A|D|G|B|HighE)_"
    r"Vel(0[123])(Finger|Pick)?_([A-G]s?\d)_01\.wav$")
ARTICULATION=re.compile(
    r"(?:^|[^a-z])(palm.?mute|muted|mute|slide|gliss|hammer.?on|pull.?off|"
    r"fret.?noise|squeak|ghost.?note|harmonic|release)(?:$|[^a-z])",re.I)


def publisher_blob_sha(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()


def meta_manifest(manifest:dict,kind:str)->dict:
    if kind not in META_NAMES:
        raise ValueError("Unknown guitar source family")
    ident,expected,positions=META_NAMES[kind]
    if manifest.get("id")!=ident or not isinstance(manifest.get("samples"),list):
        raise ValueError("Wrong publisher guitar manifest")
    counts=Counter()
    strings=set()
    pair_layers={}
    found_articulations=[]
    names=set()
    for source in manifest["samples"]:
        name=source.get("file")
        if not isinstance(name,str) or name in names:
            raise ValueError("Missing or duplicate original guitar recording")
        names.add(name)
        m=NAME.fullmatch(name)
        if m is None or m[1].lower()!=kind:
            raise ValueError("Unexpected source naming or region")
        strings.add(m[2])
        counts[f"Vel{m[3]}{m[4] or ''}"]+=1
        pair_layers.setdefault((m[2],m[5]),set()).add(m[3]+(m[4] or ""))
        if ARTICULATION.search(name):
            found_articulations.append(name)
    if len(names)!=expected or len(pair_layers)!=positions or strings!=STRINGS:
        raise ValueError("Original publisher source completeness failed")
    expected_layers=(
        {"01","02","03"} if kind=="steel" else
        {"01Finger","02Pick","03Pick"})
    if any(layers!=expected_layers for layers in pair_layers.values()):
        raise ValueError("Unpaired source velocity/technique layers")
    return {
        "source":ident, "recorded_note_count":len(names),
        "physical_string_pitch_positions":positions,
        "distinct_strings":len(strings), "velocity_techniques":dict(sorted(counts.items())),
        "dedicated_articulation_filename_matches":found_articulations,
        "finding":"Only pitched plucks by string/layer detected; this is not proof of absent non-labelled sounds."
    }


def _chunks(file,start:int,end:int):
    """Walk RIFF chunks without reading full instrument PCM into memory."""
    pos=start
    while pos+8<=end:
        file.seek(pos)
        head=file.read(8)
        if len(head)!=8:
            raise ValueError("Truncated RIFF header")
        code,size=struct.unpack("<4sI",head)
        at=pos+8
        if at+size>end:
            raise ValueError("Truncated RIFF payload")
        yield code,at,size
        pos=at+size+(size&1)
    if pos!=end:
        raise ValueError("Misaligned RIFF chunk sequence")


def sf2_inventory(path:Path)->dict:
    """Read SF2 metadata/zone headers, skipping sample PCM by seeking."""
    path=Path(path)
    with path.open("rb") as f:
        header=f.read(12)
        if len(header)!=12:
            raise ValueError("Truncated SF2")
        typ,size,kind=struct.unpack("<4sI4s",header)
        if typ!=b"RIFF" or kind!=b"sfbk" or size+8!=path.stat().st_size:
            raise ValueError("Not a complete RIFF sfbk SoundFont")
        pdta={}
        info={}
        for code,at,n in _chunks(f,12,size+8):
            if code!=b"LIST" or n<4:
                continue
            f.seek(at)
            list_type=f.read(4)
            if list_type not in (b"INFO",b"pdta"):
                continue
            for child,datapos,count in _chunks(f,at+4,at+n):
                if list_type==b"INFO" and child in (b"INAM",b"ICRD",b"IENG"):
                    f.seek(datapos)
                    info[child.decode()]=f.read(min(count,512)).split(b"\0")[0].decode("latin1")
                if list_type==b"pdta" and child in (
                    b"phdr",b"inst",b"ibag",b"igen",b"shdr"):
                    if count>4_000_000:
                        raise ValueError("Unreasonable SF2 metadata size")
                    f.seek(datapos)
                    pdta[child.decode("ascii")]=f.read(count)
    layouts={"phdr":38,"inst":22,"ibag":4,"igen":4,"shdr":46}
    if any(k not in pdta or len(pdta[k])%v or len(pdta[k])<v*2
           for k,v in layouts.items()):
        raise ValueError("Incomplete SoundFont metadata tables: "+repr(
            {k:len(v) for k,v in pdta.items()}))
    inst_names=[
        pdta["inst"][i:i+20].split(b"\0")[0].decode("latin1").strip()
        for i in range(0,len(pdta["inst"])-22,22)]
    preset_names=[
        pdta["phdr"][i:i+20].split(b"\0")[0].decode("latin1").strip()
        for i in range(0,len(pdta["phdr"])-38,38)]
    samples=[
        pdta["shdr"][i:i+20].split(b"\0")[0].decode("latin1").strip()
        for i in range(0,len(pdta["shdr"])-46,46)]
    ops=Counter(struct.unpack_from("<H",pdta["igen"],i)[0]
                for i in range(0,len(pdta["igen"]),4))
    if not samples or not inst_names or not preset_names or not ops[53]:
        raise ValueError("SoundFont has no playable sampleID zones")
    named={x for x in (*inst_names,*preset_names,*samples)
           if ARTICULATION.search(x)}
    return {
        "file_bytes":path.stat().st_size,
        "bank_name":info.get("INAM",""),
        "preset_count":len(preset_names),
        "instrument_count":len(inst_names),
        "sample_header_count":len(samples),
        "instrument_sampleID_zone_count":ops[53],
        "pitch_bend_or_sliding_recordings_named":sorted(named),
        "sample_names":samples,
        "preset_names":preset_names,
        "instrument_names":inst_names,
        "finding":"SF2 names and IGEN structure only; a named slide/mute is not proof of a playable switching mechanism."
    }


def sfz_regions(text:str)->dict:
    no_comment=re.sub(r"(?m)//[^\n]*","",text)
    regions=re.split(r"<region>",no_comment)[1:]
    sample_names=re.findall(r"\bsample=([^\s<>]+)",no_comment)
    if not sample_names or len(sample_names)!=len(regions):
        raise ValueError("Unmapped original SFZ regions")
    trigger=list(re.findall(r"\btrigger=([^\s<>]+)",no_comment))
    named=[s for s in sample_names if ARTICULATION.search(s)]
    return {"note_region_count":len(regions),
            "source_sample_paths":sample_names,
            "named_special_articulation_files":named,
            "release_trigger_region_count":sum(x.lower()=="release" for x in trigger),
            "loop_continuous_declared":"loop_continuous" in no_comment,
            "finding":"Original SFZ source zones only; no inferred legato or pitch-slide source."}


def report(metas:dict[str,dict],fonts:dict[str,Path],sfzs:dict[str,str])->dict:
    guitar={k:meta_manifest(v,k) for k,v in metas.items()}
    sf2={k:sf2_inventory(v) for k,v in fonts.items()}
    sfz={k:sfz_regions(v) for k,v in sfzs.items()}
    return {
        "guitar_meta":guitar,
        "soundfonts":sf2,
        "source_sfz":sfz,
        "recommendation":"Audit completed: do not mislabel velocity/timbre as palm-mute or simulate a bass slide as recorded. Next isolated test: short-note acoustic damping with explicit technique tag; never steal another note's decay.",
        "limitations":"Static source inventory: need controlled audio A/B to evaluate sound or switch behavior."
    }


if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--source-root",type=Path,required=True)
    p.add_argument("--fonts",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    metas={k:json.loads((a.source_root/f"{v[0]}.json").read_text())
           for k,v in META_NAMES.items()}
    sfzs={k:(a.source_root/f"{k}.sfz").read_text()
          for k in ("electric_small","finger_bass","picked_bass")}
    fonts={k:a.fonts/f"{k}.sf2"
           for k in ("electric_small","finger_bass","picked_bass")}
    output=report(metas,fonts,sfzs)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(output,indent=2))
    print(json.dumps({
        "meta":{k:v["recorded_note_count"] for k,v in output["guitar_meta"].items()},
        "sfz":{k:v["note_region_count"] for k,v in output["source_sfz"].items()},
        "sf2":{k:{"samples":v["sample_header_count"],"named_special":v["pitch_bend_or_sliding_recordings_named"]}
                for k,v in output["soundfonts"].items()}
        },indent=2))
