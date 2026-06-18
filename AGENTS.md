# AGENTS.md

Guidance for coding agents working in this repository.

## Project Purpose

This repo is a drum practice archive. Each practice video gets a summary page, and each exercise gets its own Markdown page with a simple count-grid pattern plus playable audio.

## Repository Structure

- `README.md`: high-level index of practice sets. Keep this concise.
- `videos/`: one summary page per practice video or lesson.
- `exercises/`: individual exercise pages.
- `audio/`: generated WAV samples.
- `midi/`: generated MIDI files.
- `templates/`: reusable Markdown templates.
- `tools/`: local generation scripts.

## Workflow for a New Practice Video

1. Add or update a video-level page in `videos/`.
2. Record metadata:
   - video title
   - producer
   - source URL
   - date practiced
   - overall difficulty
3. Put the shared pattern on the video page.
4. Add a concise exercise table linking to individual exercise pages.
5. Add one row to the `README.md` practice set table. Do not list every exercise in the root README.

## Workflow for a New Exercise

1. Create a Markdown page under the appropriate `exercises/` subdirectory.
2. Include:
   - source link
   - video title
   - video producer
   - date practiced
   - tempo
   - time signature
   - pattern grid
   - difficulty
   - embedded audio player
   - WAV and MIDI links
3. Keep exercise pages focused. Do not add `Notes` or `Next Goal` sections unless explicitly requested.
4. Update the relevant video-level table with the new exercise.

## Drum Pattern Convention

For this first exercise family:

- Time: 4/4
- Hi-hat: straight eighth notes
- Snare: beats 2 and 4
- Kick: varies by exercise

Use this count grid:

```text
Count: 1 & 2 & 3 & 4 &
HH:    x x x x x x x x
S:         o       o
K:
```

Kick step mapping for `tools/generate_drum_sample.py`:

- `0`: beat 1
- `1`: & of 1
- `2`: beat 2
- `3`: & of 2
- `4`: beat 3
- `5`: & of 3
- `6`: beat 4
- `7`: & of 4

## Audio Generation

Use the local generator:

```bash
python3 tools/generate_drum_sample.py 80 4 0,4 audio/kick-variations/example.wav midi/kick-variations/example.mid
```

Arguments:

1. BPM
2. Number of bars
3. Comma-separated kick steps
4. WAV output path
5. MIDI output path

After generating a WAV, play it immediately so the user can verify it:

```bash
afplay audio/kick-variations/example.wav
```

## Markdown Audio

Use an embedded HTML audio control in exercise pages:

```html
<audio controls src="../../audio/kick-variations/example.wav">
  Your browser does not support the audio element.
</audio>
```

Also include direct links:

```md
- [Download WAV](../../audio/kick-variations/example.wav)
- [MIDI file](../../midi/kick-variations/example.mid)
```

## Current Practice Set

- Title: `10 Beginner Beats To Get You Playing Quickly!`
- Producer: `Rob Brown`
- Source: `https://www.youtube.com/watch?v=nt7re7wGzqc`
- Date practiced: `2026-06-18`
- Shared pattern: straight eighth-note hi-hat, snare on 2 and 4, kick variations

