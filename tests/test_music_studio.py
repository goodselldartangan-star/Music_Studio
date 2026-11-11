"""Offline quality gates: no tokens, music credits, or third-party network calls."""
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import music_studio as studio

PLAN = json.loads((ROOT / 'examples' / 'the_last_ferry_bell.json').read_text())


class MockResponse(io.BytesIO):
    pass


class MusicStudioTests(unittest.TestCase):
    def test_profiles_are_distinct_and_reference_free(self):
        self.assertEqual(set(studio.PROFILES), {'indie_pop_rock', 'electronic_story_pop', 'hybrid'})
        self.assertNotEqual(studio.PROFILES['indie_pop_rock']['lead_voice'],
                            studio.PROFILES['electronic_story_pop']['lead_voice'])
        self.assertFalse(any("Don't Let Me" in str(p) for p in studio.PROFILES.values()))

    def test_writing_brief_guides_gpt_without_copyrighted_sources(self):
        brief = studio.writing_brief('A lighthouse keeper has to return a lost key', 'hybrid')
        self.assertIn('fully ORIGINAL', brief)
        self.assertIn('lighthouse keeper', brief)
        self.assertIn('unforgettable', brief)
        self.assertIn('No covers', brief)
        with self.assertRaises(ValueError):
            studio.writing_brief('', 'hybrid')

    def test_valid_plan_and_payload_contract(self):
        meta = studio.validate_plan(PLAN)
        self.assertEqual(meta['duration_seconds'], 223)
        req = studio.music_payload(PLAN)
        self.assertEqual(req['model_id'], 'music_v2_5')
        self.assertNotIn('prompt', req)
        self.assertNotIn('music_length_ms', req)
        self.assertNotIn('title', req['composition_plan'])
        self.assertEqual(len(req['composition_plan']['chunks']), 9)

    def test_invalid_plans_block_all_paid_calls(self):
        for bad in ('bpm', 'chorus', 'too_short', 'styles', 'missing_label'):
            plan = copy.deepcopy(PLAN)
            if bad == 'bpm':
                plan['bpm'] = 1000
            elif bad == 'chorus':
                for ch in plan['chunks']:
                    ch['text'] = ch['text'].replace('Chorus', 'Interlude')
            elif bad == 'too_short':
                plan['chunks'][0]['duration_ms'] = 100
            elif bad == 'styles':
                plan['chunks'][0]['positive_styles'] = 'piano'
            else:
                plan['chunks'][0]['text'] = 'wrong label'
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                studio.render_music(plan, ROOT / 'never.mp3', opener=lambda *_args, **_kw: self.fail('network called'))

    def test_dry_run_never_contacts_provider_or_needs_secret(self):
        with patch.dict(os.environ, {'ELEVENLABS_API_KEY': ''}):
            r = studio.render_music(PLAN, ROOT / 'never.mp3', dry_run=True,
                                    opener=lambda *_args, **_kw: self.fail('network called'))
        self.assertEqual(r['mode'], 'dry_run')
        self.assertEqual(r['expected_seconds'], 223)

    def test_render_requires_key_and_does_not_create_file(self):
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ, {'ELEVENLABS_API_KEY': ''}):
            path = Path(d) / 'song.mp3'
            with self.assertRaises(RuntimeError):
                studio.render_music(PLAN, path, opener=lambda *_a, **_kw: self.fail('network called'))
            self.assertFalse(path.exists())

    def test_mocked_full_song_provider_stream_and_atomic_promotion(self):
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ, {'ELEVENLABS_API_KEY': 'fake-test-key'}):
            path = Path(d) / 'song.mp3'
            requests = []
            def mock_provider(request, timeout):
                requests.append((request,timeout))
                return MockResponse(b'ID3' + b'\0' * 16384)
            with patch.object(studio, 'quality_gate', return_value={'passed': True}) as checker:
                result = studio.render_music(PLAN, path, opener=mock_provider)
            self.assertTrue(path.read_bytes().startswith(b'ID3'))
            self.assertFalse(path.with_suffix('.mp3.partial').exists())
            self.assertTrue(result['qa']['passed'])
            self.assertEqual(requests[0][0].get_header('Xi-api-key'), 'fake-test-key')
            self.assertEqual(json.loads(requests[0][0].data)['model_id'], 'music_v2_5')
            checker.assert_called_once()

    def test_rejected_provider_response_does_not_overwrite_master(self):
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ, {'ELEVENLABS_API_KEY': 'fake-test-key'}):
            path = Path(d) / 'song.mp3'
            path.write_bytes(b'original-good-master')
            with patch.object(studio, 'quality_gate', side_effect=ValueError('not audio')):
                with self.assertRaises(ValueError):
                    studio.render_music(PLAN, path, opener=lambda *_a, **_kw: MockResponse(b'bad audio'))
            self.assertEqual(path.read_bytes(), b'original-good-master')
            self.assertFalse(path.with_suffix('.mp3.partial').exists())

    def test_gpt_plan_parser_and_mocked_gpt_request(self):
        answer = {'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': json.dumps(PLAN)}]}]}
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'fake-test-key'}):
            requests = []
            def fake_open(request, timeout):
                requests.append(request)
                return MockResponse(json.dumps(answer).encode())
            generated = studio.generate_plan('A lighthouse across the bay', 'indie_pop_rock', opener=fake_open)
        self.assertEqual(generated['title'], 'The Last Ferry Bell')
        self.assertIn('responses', requests[0].full_url)
        self.assertEqual(requests[0].get_header('Authorization'), 'Bearer fake-test-key')
        self.assertNotIn('file', json.loads(requests[0].data))
        with self.assertRaises(ValueError):
            studio.parse_gpt_output({'output': []})

    @unittest.skipUnless(subprocess.run(['which', 'ffmpeg'], capture_output=True).returncode == 0,
                         'ffmpeg required for real MP3 decoder gate')
    def test_real_mp3_decoder_gate_and_silence_rejection(self):
        with tempfile.TemporaryDirectory() as d:
            good = Path(d) / 'good.mp3'
            silent = Path(d) / 'silent.mp3'
            subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi',
                 '-i','sine=frequency=440:duration=8:sample_rate=48000', '-ac', '2',
                 '-codec:a','libmp3lame','-b:a','192k',str(good)],check=True)
            result = studio.quality_gate(good, 8)
            self.assertTrue(result['passed'])
            self.assertEqual(result['codec'], 'mp3')
            with self.assertRaises(ValueError):
                studio.quality_gate(good, 100)
            subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi',
                 '-i','anullsrc=r=48000:cl=stereo','-t','8',
                 '-codec:a','libmp3lame','-b:a','192k',str(silent)],check=True)
            with self.assertRaises(ValueError):
                studio.quality_gate(silent, 8)


if __name__ == '__main__':
    unittest.main()
