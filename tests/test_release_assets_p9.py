"""P9 credential-free mock of gh release asset safety and repeatability."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT=Path(__file__).resolve().parents[1]/'tools/upload_release_if_missing.sh'
FAKE_GH='''#!/usr/bin/env python3
import json,os,sys
from pathlib import Path
state=Path(os.environ["MOCK_GH_STATE"])
info=json.loads(state.read_text())
args=sys.argv[1:]
if args[:2]==["release","view"]:
    print("\\n".join(info["assets"]))
elif args[:2]==["release","upload"]:
    if "--clobber" in args:
        raise SystemExit("Release overwrite forbidden")
    name=Path(args[3]).name
    if name in info["assets"]:
        raise SystemExit("Asset already exists")
    info["assets"].append(name)
    info["uploads"].append(name)
    state.write_text(json.dumps(info))
else:
    raise SystemExit("Unsupported fake gh call: "+repr(args))
'''


class ReleasePreservationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        fake=self.root/'gh'
        fake.write_text(FAKE_GH)
        fake.chmod(0o755)
        self.state=self.root/'release.json'
        self.env=os.environ.copy()
        self.env['PATH']=str(self.root)+os.pathsep+self.env['PATH']
        self.env['MOCK_GH_STATE']=str(self.state)
        for name in ('old.mp3','new.mp3'):
            (self.root/name).write_bytes(b'fixture'+name.encode())

    def run_publisher(self,*names):
        return subprocess.run(['bash',str(SCRIPT),'preserved-release',
                               *(str(self.root/name) for name in names)],
                              env=self.env,capture_output=True,text=True)

    def test_existing_assets_never_overwritten_and_repeated_runs_are_noops(self):
        self.state.write_text(json.dumps({'assets':['old.mp3'],'uploads':[]}))
        for _ in range(2):
            r=self.run_publisher('old.mp3','new.mp3')
            self.assertEqual(r.returncode,0,r.stderr)
        saved=json.loads(self.state.read_text())
        self.assertEqual(saved['uploads'],['new.mp3'])
        self.assertEqual(saved['assets'],['old.mp3','new.mp3'])

    def test_same_new_asset_twice_only_uploaded_once(self):
        self.state.write_text(json.dumps({'assets':[],'uploads':[]}))
        result=self.run_publisher('new.mp3','new.mp3')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(self.state.read_text())['uploads'],['new.mp3'])

    def test_missing_input_is_rejected_before_gh_upload(self):
        self.state.write_text(json.dumps({'assets':[],'uploads':[]}))
        result=self.run_publisher('does-not-exist.mp3')
        self.assertEqual(result.returncode,3)
        self.assertEqual(json.loads(self.state.read_text())['uploads'],[])

    def test_no_clobber_in_workflow_publishing(self):
        repo=SCRIPT.parents[1]
        workflow=(repo/'.github/workflows/music-studio-v7.yml').read_text()
        self.assertNotIn('gh release upload music-studio-v7-instrument-fit \\',workflow)
        self.assertNotIn('--clobber',workflow)
        self.assertIn('upload_release_if_missing.sh',workflow)


if __name__=='__main__':unittest.main()
