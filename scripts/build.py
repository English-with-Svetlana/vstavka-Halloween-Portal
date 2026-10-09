#!/usr/bin/env python3
"""Build and verify local web media. Requires ffmpeg and ffprobe on PATH."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'Vstavka-Halloween-Portal.mp4'
ASSETS = ROOT / 'assets'

def run(*args):
    return subprocess.check_output([str(a) for a in args], text=True)

def probe(path):
    return json.loads(run('ffprobe', '-v', 'error', '-count_frames', '-show_streams', '-show_format', '-of', 'json', path))

def frames(path):
    return json.loads(run('ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_frames', '-show_entries', 'frame=best_effort_timestamp_time,pkt_duration_time,key_frame', '-of', 'json', path))['frames']

def atoms(path):
    result = []
    with path.open('rb') as f:
        while header := f.read(8):
            size, kind = struct.unpack('>I4s', header)
            if size == 1:
                size = struct.unpack('>Q', f.read(8))[0]
                header_size = 16
            else:
                header_size = 8
            result.append(kind.decode('ascii'))
            if not size:
                break
            f.seek(size - header_size, 1)
    return result

def publish(path, name):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    target = ASSETS / f'{name}.{digest}{path.suffix}'
    target.write_bytes(path.read_bytes())
    return target

def main():
    original = probe(SOURCE)
    before = next(s for s in original['streams'] if s['codec_type'] == 'video')
    assert (before['width'], before['height'], before['display_aspect_ratio']) == (1920, 1080, '16:9')
    ASSETS.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as work:
        video = Path(work) / 'transition.mp4'
        poster = Path(work) / 'poster.jpg'
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'warning', '-y', '-i', str(SOURCE),
                        '-map', '0:v:0', '-an', '-sn', '-dn', '-map_metadata', '-1',
                        '-vf', 'scale=1280:720:flags=lanczos', '-c:v', 'libx264', '-preset', 'slow', '-crf', '23', '-pix_fmt', 'yuv420p',
                        '-g', '48', '-keyint_min', '24', '-fps_mode', 'passthrough',
                        '-movflags', '+faststart', str(video)], check=True)
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(video),
                        '-frames:v', '1', '-q:v', '7', str(poster)], check=True)
        final = probe(video)
        assert len(final['streams']) == 1 and final['streams'][0]['codec_type'] == 'video'
        after = final['streams'][0]
        for key in ('avg_frame_rate', 'nb_read_frames', 'duration', 'display_aspect_ratio'):
            assert before[key] == after[key], (key, before[key], after[key])
        assert (after['width'], after['height']) == (1280, 720)
        assert after['codec_name'] == 'h264' and after['pix_fmt'] == 'yuv420p'
        a, b = frames(SOURCE), frames(video)
        assert len(a) == len(b) == 192
        assert [f['best_effort_timestamp_time'] for f in a] == [f['best_effort_timestamp_time'] for f in b]
        box_order = atoms(video)
        assert box_order.index('moov') < box_order.index('mdat')
        subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(video), '-f', 'null', '-'], check=True)
        # Compare every corresponding decoded frame: quality and ordering, without modifying timing.
        comparison = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(SOURCE), '-i', str(video),
                                     '-lavfi', '[0:v]scale=1280:720:flags=lanczos[reference];[reference][1:v]ssim', '-an', '-f', 'null', '-'],
                                    capture_output=True, text=True, check=True)
        ssim = next(line for line in comparison.stderr.splitlines() if 'SSIM Y:' in line)
        target_video, target_poster = publish(video, 'transition'), publish(poster, 'poster')
        html = (ROOT / 'scripts/index.template.html').read_text()
        html = html.replace('__VIDEO__', target_video.relative_to(ROOT).as_posix()).replace('__POSTER__', target_poster.relative_to(ROOT).as_posix())
        (ROOT / 'index.html').write_text(html)
        def summary(p, info):
            v = next(s for s in info['streams'] if s['codec_type'] == 'video')
            return {'file': p.relative_to(ROOT).as_posix(), 'bytes': p.stat().st_size,
                    'duration_seconds': float(v['duration']), 'resolution': [v['width'], v['height']],
                    'frames': int(v['nb_read_frames']), 'fps': v['avg_frame_rate'], 'video_bitrate': int(v['bit_rate']),
                    'codec': v['codec_name'], 'pixel_format': v['pix_fmt'],
                    'audio_streams': sum(s['codec_type'] == 'audio' for s in info['streams'])}
        report = {'original': summary(SOURCE, original), 'optimized': summary(target_video, final),
                  'reduction_percent': round((1 - target_video.stat().st_size / SOURCE.stat().st_size) * 100, 2),
                  'poster': {'file': target_poster.relative_to(ROOT).as_posix(), 'bytes': target_poster.stat().st_size, 'resolution': [1280, 720]},
                  'original_keyframe_times': [f['best_effort_timestamp_time'] for f in a if f['key_frame']],
                  'optimized_keyframe_times': [f['best_effort_timestamp_time'] for f in b if f['key_frame']],
                  'frame_timestamps_equal': True, 'full_decode_passed': True, 'faststart_atom_order': box_order,
                  'frame_comparison': ssim, 'browser_playback': 'UNVERIFIED: no browser available', 'genially_embedding': 'UNVERIFIED'}
        (ROOT / 'media-report.json').write_text(json.dumps(report, indent=2) + '\n')
        # Remove only stale generated assets after valid media and HTML are published.
        for pattern in ('transition.*.mp4', 'poster.*.jpg'):
            for old in ASSETS.glob(pattern):
                if old not in (target_video, target_poster):
                    old.unlink()
        print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
