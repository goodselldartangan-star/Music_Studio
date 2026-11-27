"""Q4.2 no-invented-articulations source parser regression tests."""
import json
import struct
import tempfile
import unittest
from pathlib import Path

from tools.audit_articulation_q42 import (
    publisher_blob_sha,meta_manifest,sf2_inventory,sfz_regions)


def _chunk(tag:bytes,body:bytes)->bytes:
    return tag+struct.pack("<I",len(body))+body+(b"\0" if len(body)%2 else b"")


def _name(name:str,size:int)->bytes:
    return name.encode().ljust(size,b"\0")


def small_sf2(path:Path,*,samples:tuple[str,...]=("E2 pluck",))->None:
    presets=_name("Bass",20)+b"\0"*18 + _name("EOP",20)+b"\0"*18
    inst=_name("Bass",20)+struct.pack("<H",0)
    inst+=_name("EOI",20)+struct.pack("<H",1)
    ibag=struct.pack("<HH",0,0)+struct.pack("<HH",1,0)
    igen=struct.pack("<HH",53,0)+struct.pack("<HH",0,0)
    shdr=b"".join(_name(name,20)+b"\0"*26 for name in (*samples,"EOS"))
    pdta=b"".join(_chunk(k,v) for k,v in (
        (b"phdr",presets),(b"inst",inst),(b"ibag",ibag),
        (b"igen",igen),(b"shdr",shdr)))
    payload=b"sfbk"+_chunk(b"LIST",b"INFO"+_chunk(b"INAM",b"Test Soundfont"))
    payload+=_chunk(b"LIST",b"pdta"+pdta)
    path.write_bytes(b"RIFF"+struct.pack("<I",len(payload))+payload)


def fake_manifest(kind:str):
    prefix="Steel" if kind=="steel" else "Nylon"
    positions=125 if kind=="steel" else 116
    # A correctly stratified three-layer synthetic source, not audio.
    pairs=[("LowE",f"C{i}") for i in range(positions)]
    layers=("01","02","03") if kind=="steel" else ("01Finger","02Pick","03Pick")
    return {"id":"meta-"+kind+"-guitar","samples":[
        {"file":f"INSGuitar{prefix}_String{string}_Vel{layer}_{pitch}_01.wav"}
        for string,pitch in pairs for layer in layers]}


class Q42SourceAuditTests(unittest.TestCase):
    def test_git_blob_identity_is_content_based(self):
        import hashlib
        value=b"licensed sound recording test fixture"
        expected=hashlib.sha1(b"blob "+str(len(value)).encode()+b"\0"+value).hexdigest()
        self.assertEqual(publisher_blob_sha(value),expected)

    def test_incorrect_guitar_manifest_is_not_mistaken_for_complete_source(self):
        source=fake_manifest("nylon")
        with self.assertRaisesRegex(ValueError,"completeness"):
            meta_manifest(source,"nylon")
        source["samples"].pop()
        with self.assertRaises(ValueError):
            meta_manifest(source,"nylon")

    def test_mute_and_slide_labels_not_inferred_from_guitar_velocity_names(self):
        source=fake_manifest("steel")
        # Use six valid strings, 125 positions, three layers each.
        strings=("LowE","A","D","G","B","HighE")
        for index,item in enumerate(source["samples"]):
            name=item["file"]
            item["file"]=name.replace("StringLowE",f"String{strings[(index//3)%6]}")
        result=meta_manifest(source,"steel")
        self.assertEqual(result["recorded_note_count"],375)
        self.assertFalse(result["dedicated_articulation_filename_matches"])
        source["samples"][0]["file"]=source["samples"][0]["file"].replace(
            "Vel01","Vel01Muted")
        with self.assertRaisesRegex(ValueError,"source naming"):
            meta_manifest(source,"steel")

    def test_original_sfz_note_and_release_zones_are_distinct(self):
        text=("<group> ampeg_release=.3\n<region> key=40 sample=finger/E.flac\n"
              "<region> key=41 sample=finger/F.flac")
        s=sfz_regions(text)
        self.assertEqual(s["note_region_count"],2)
        self.assertEqual(s["release_trigger_region_count"],0)
        self.assertEqual(s["named_special_articulation_files"],[])
        with self.assertRaises(ValueError):
            sfz_regions("<region> key=40")

    def test_sf2_parser_reads_metadata_without_decoding_pcm(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"test.sf2"
            small_sf2(path)
            result=sf2_inventory(path)
            self.assertEqual(result["bank_name"],"Test Soundfont")
            self.assertEqual(result["sample_header_count"],1)
            self.assertEqual(result["instrument_sampleID_zone_count"],1)
            self.assertEqual(result["pitch_bend_or_sliding_recordings_named"],[])
            path.write_bytes(path.read_bytes()[:-2])
            with self.assertRaises(ValueError):
                sf2_inventory(path)


if __name__=="__main__":
    unittest.main()
