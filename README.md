# Halloween Portal transition

A silent, continuously looping video page for a 1280 × 720 Genially iframe. The page uses only local, relative assets and can be published at this project's existing GitHub Pages address. No repository settings, remotes, commits, pushes, or deployment are part of this change.

## Build and verify

Install FFmpeg (including ffprobe), Python 3, and Node.js, then run:

```sh
python3 scripts/build.py
node scripts/verify.mjs
python3 -m http.server 8765 --bind 127.0.0.1
```

Open `http://127.0.0.1:8765/` or `http://127.0.0.1:8765/scripts/iframe-test.html`. The latter is a 1280 × 720 iframe test harness. Observe more than 24 seconds to see at least three complete 8-second cycles, then refresh. Check motion, loop boundaries, controls, and browser console/media errors. Also test in the actual Genially presentation.

## Media workflow

The original MP4 stays unchanged. The build encodes only the video stream to H.264/yuv420p using Lanczos scaling to the slide's 1280 × 720 resolution, CRF 23, the slow preset, maximum 48-frame keyframe spacing, and faststart. Frame-rate conversion, trimming, and scene changes are not applied. Every decoded frame's presentation timestamp is compared to the original. The build checks full decoding, stream count, frame count, duration, aspect ratio, frame rate, MP4 atom order, and SSIM against the source scaled to the output size.

A JPEG poster is extracted from the optimized video's actual first frame, at the same dimensions. SHA-256-based asset filenames and generated HTML references change together on rebuilding. Stale generated media is removed only after successful validation and publication. The exact media metrics and checks are recorded in `media-report.json`.

## Playback and layout

Native `autoplay muted playsinline loop preload="auto"` handles playback. JavaScript explicitly enables autoplay, looping, inline playback, and default/current mute; volume is zero and controls are disabled. Play-promise rejections are handled without showing buttons. Media readiness, returning page visibility, and page restoration can retry paused playback. Already playing video is left alone. There are no seeks, end handlers, overlays, frame gates, artificial delays, pause calls, or disappearance timers.

The centered stage preserves the 16:9 ratio using contain sizing, with a transparent page and no scrolling. At 1280 × 720 or another 16:9 iframe size it fills the frame exactly. Other frame shapes leave transparent unused space to preserve all content without distortion or cropping. The video itself is opaque; transparent HTML does not remove the source scene's background.

## Publication and embedding

Publish this folder's files to this project's existing GitHub Pages location, keeping `index.html` and `assets/` together. Embed that existing URL in Genially at 16:9. If custom iframe markup is available, include `allow="autoplay"` and remove the iframe border. No external video host is needed.

No connected real browser was available during implementation. Actual autoplay, motion, multiple loops, refresh behavior, and Genially embedding remain UNVERIFIED. Static checks and media verification do not prove browser playback. Browser or parent-frame autoplay policies can still deny playback; the native first-frame poster remains visible in that case. Native looping avoids intentional pauses, but no visual loop-boundary claim is made without browser testing. The animation's original first/last-frame composition is preserved, rather than editing the scene to create a new seam.

The local Inquisitor reference was inspected for its centered 16:9 stage and native video setup. This project uses that layout approach with a transparent background and only the native poster. No local Tunnel project was found in the inspected Desktop/Documents locations; the supplied reference websites were inaccessible from the available web tool.
