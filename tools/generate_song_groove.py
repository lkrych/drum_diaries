#!/usr/bin/env python3
import math
import random
import struct
import sys
import wave
from pathlib import Path


SAMPLE_RATE = 44100
CHANNEL = 9
PPQ = 480
DEFAULT_HH_STEPS = [0, 2, 4, 6, 8, 10, 12, 14]
ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DIR = ROOT / "samples" / "hydrogen-gmrockkit"
SAMPLES = {}


def add_sample(buffer, index, value):
    if 0 <= index < len(buffer):
        buffer[index] += value


def load_wav_sample(path):
    with wave.open(str(path), "rb") as wav:
        channels = wav.getnchannels()
        width = wav.getsampwidth()
        rate = wav.getframerate()
        frames = wav.readframes(wav.getnframes())

    if width != 2:
        raise ValueError(f"unsupported sample width for {path}: {width}")

    values = struct.unpack("<" + "h" * (len(frames) // 2), frames)
    mono = []
    for i in range(0, len(values), channels):
        mono.append(sum(values[i : i + channels]) / channels / 32768.0)

    if rate == SAMPLE_RATE:
        return mono

    ratio = rate / SAMPLE_RATE
    resampled = []
    for i in range(int(len(mono) / ratio)):
        source_index = min(int(i * ratio), len(mono) - 1)
        resampled.append(mono[source_index])
    return resampled


def load_samples():
    sample_paths = {
        "kick": SAMPLE_DIR / "Kick-Med.wav",
        "snare": SAMPLE_DIR / "Snare-Med.wav",
        "hh": SAMPLE_DIR / "HatClosed-Med.wav",
        "oh": SAMPLE_DIR / "HatOpen-Med.wav",
    }
    for name, path in sample_paths.items():
        if path.exists():
            SAMPLES[name] = load_wav_sample(path)


def mix_sample(buffer, start, sample_name, gain=1.0):
    sample = SAMPLES.get(sample_name)
    if not sample:
        return False

    for i, value in enumerate(sample):
        add_sample(buffer, start + i, value * gain)
    return True


def synth_kick(buffer, start):
    if mix_sample(buffer, start, "kick", 1.0):
        return

    length = int(0.28 * SAMPLE_RATE)
    for i in range(length):
        t = i / SAMPLE_RATE
        amp = math.exp(-t * 18.0)
        freq = 105.0 * math.exp(-t * 18.0) + 42.0
        phase = 2.0 * math.pi * freq * t
        click = 0.45 * math.exp(-t * 160.0) if i < int(0.03 * SAMPLE_RATE) else 0.0
        add_sample(buffer, start + i, (math.sin(phase) * 0.95 + click) * amp)


def synth_snare(buffer, start, velocity=1.0):
    if mix_sample(buffer, start, "snare", velocity):
        return

    length = int(0.22 * SAMPLE_RATE)
    for i in range(length):
        t = i / SAMPLE_RATE
        noise_env = math.exp(-t * 20.0)
        tone_env = math.exp(-t * 28.0)
        noise = random.uniform(-1.0, 1.0) * noise_env * 0.65
        tone = math.sin(2.0 * math.pi * 185.0 * t) * tone_env * 0.35
        add_sample(buffer, start + i, (noise + tone) * velocity)


def synth_hihat(buffer, start):
    if mix_sample(buffer, start, "hh", 0.85):
        return

    length = int(0.075 * SAMPLE_RATE)
    for i in range(length):
        t = i / SAMPLE_RATE
        env = math.exp(-t * 65.0)
        noise = random.uniform(-1.0, 1.0)
        shimmer = math.sin(2.0 * math.pi * 8200.0 * t) * 0.22
        add_sample(buffer, start + i, (noise * 0.45 + shimmer) * env)


def synth_open_hihat(buffer, start, style="tight"):
    if mix_sample(buffer, start, "oh", 0.9):
        return

    if style == "sizzle":
        length = int(0.52 * SAMPLE_RATE)
        decay = 6.5
        noise_level = 0.30
        shimmer_level = 0.36
        shimmer_freq = 9100.0
    else:
        length = int(0.24 * SAMPLE_RATE)
        decay = 16.0
        noise_level = 0.28
        shimmer_level = 0.22
        shimmer_freq = 6800.0

    for i in range(length):
        t = i / SAMPLE_RATE
        env = math.exp(-t * decay)
        noise = random.uniform(-1.0, 1.0)
        shimmer = math.sin(2.0 * math.pi * shimmer_freq * t) * shimmer_level
        add_sample(buffer, start + i, (noise * noise_level + shimmer) * env)


def parse_steps(value):
    if not value:
        return []
    return [int(step) for step in value.split(",") if step]


def parse_pattern(pattern_spec):
    bars = []
    for bar_spec in pattern_spec.split("|"):
        bar = {"hh": DEFAULT_HH_STEPS[:], "oh": [], "ohs": [], "s": [], "k": []}
        for part in bar_spec.split(";"):
            if not part:
                continue
            key, _, value = part.partition("=")
            if key not in bar:
                raise ValueError(f"unknown pattern key: {key}")
            bar[key] = parse_steps(value)
        bars.append(bar)
    return bars


def write_wav(path, bpm, bars):
    random.seed(23)
    seconds_per_beat = 60.0 / bpm
    total_samples = int((len(bars) * 4 * seconds_per_beat + 0.75) * SAMPLE_RATE)
    buffer = [0.0] * total_samples

    for bar_index, bar in enumerate(bars):
        bar_offset = bar_index * 4.0
        for step in bar["hh"]:
            beat_offset = bar_offset + step * 0.25
            index = int(beat_offset * seconds_per_beat * SAMPLE_RATE)
            synth_hihat(buffer, index)
        for step in bar["oh"]:
            beat_offset = bar_offset + step * 0.25
            index = int(beat_offset * seconds_per_beat * SAMPLE_RATE)
            synth_open_hihat(buffer, index)
        for step in bar["ohs"]:
            beat_offset = bar_offset + step * 0.25
            index = int(beat_offset * seconds_per_beat * SAMPLE_RATE)
            synth_open_hihat(buffer, index, "sizzle")
        for step in bar["s"]:
            beat_offset = bar_offset + step * 0.25
            index = int(beat_offset * seconds_per_beat * SAMPLE_RATE)
            synth_snare(buffer, index)
        for step in bar["k"]:
            beat_offset = bar_offset + step * 0.25
            index = int(beat_offset * seconds_per_beat * SAMPLE_RATE)
            synth_kick(buffer, index)

    peak = max(max(buffer), abs(min(buffer)), 1.0)
    scale = 0.88 / peak

    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        frames = bytearray()
        for sample in buffer:
            frames.extend(struct.pack("<h", int(max(-1.0, min(1.0, sample * scale)) * 32767)))
        wav.writeframes(frames)


def var_len(value):
    bytes_out = [value & 0x7F]
    value >>= 7
    while value:
        bytes_out.insert(0, (value & 0x7F) | 0x80)
        value >>= 7
    return bytes(bytes_out)


def midi_event(delta, status, data1, data2):
    return var_len(delta) + bytes([status, data1, data2])


def write_midi(path, bpm, bars):
    events = bytearray()
    tempo = int(60_000_000 / bpm)
    events.extend(b"\x00\xff\x51\x03" + tempo.to_bytes(3, "big"))
    events.extend(b"\x00\xff\x58\x04\x04\x02\x18\x08")

    notes = []
    for bar_index, bar in enumerate(bars):
        base = bar_index * 4 * PPQ
        for step in bar["hh"]:
            notes.append((base + step * PPQ // 4, 42, 62, PPQ // 8))
        for step in bar["oh"]:
            notes.append((base + step * PPQ // 4, 46, 72, PPQ // 2))
        for step in bar["ohs"]:
            notes.append((base + step * PPQ // 4, 46, 72, PPQ // 2))
        for step in bar["s"]:
            notes.append((base + step * PPQ // 4, 38, 92, PPQ // 4))
        for step in bar["k"]:
            notes.append((base + step * PPQ // 4, 36, 108, PPQ // 4))

    midi_messages = []
    for tick, note, velocity, duration in notes:
        midi_messages.append((tick, 0x90 | CHANNEL, note, velocity))
        midi_messages.append((tick + duration, 0x80 | CHANNEL, note, 0))

    last_tick = 0
    for tick, status, note, velocity in sorted(midi_messages, key=lambda item: (item[0], item[1])):
        events.extend(midi_event(tick - last_tick, status, note, velocity))
        last_tick = tick
    events.extend(var_len(0) + b"\xff\x2f\x00")

    path.parent.mkdir(parents=True, exist_ok=True)
    header = b"MThd" + struct.pack(">IHHH", 6, 0, 1, PPQ)
    track = b"MTrk" + struct.pack(">I", len(events)) + bytes(events)
    path.write_bytes(header + track)


def main():
    if len(sys.argv) != 5:
        print(
            "usage: generate_song_groove.py BPM PATTERN_SPEC WAV_PATH MIDI_PATH\n"
            "example pattern: 'hh=0,2,4,6,8,10,12,14;oh=0;ohs=6;s=4,12;k=0,3,8'",
            file=sys.stderr,
        )
        return 2

    load_samples()

    bpm = int(sys.argv[1])
    bars = parse_pattern(sys.argv[2])
    wav_path = Path(sys.argv[3])
    midi_path = Path(sys.argv[4])

    write_wav(wav_path, bpm, bars)
    write_midi(midi_path, bpm, bars)
    print(f"wrote {wav_path}")
    print(f"wrote {midi_path}")


if __name__ == "__main__":
    raise SystemExit(main())
