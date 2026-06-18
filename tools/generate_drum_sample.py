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


def add_sample(buffer, index, value):
    if 0 <= index < len(buffer):
        buffer[index] += value


def synth_kick(buffer, start):
    length = int(0.28 * SAMPLE_RATE)
    for i in range(length):
        t = i / SAMPLE_RATE
        amp = math.exp(-t * 18.0)
        freq = 105.0 * math.exp(-t * 18.0) + 42.0
        phase = 2.0 * math.pi * freq * t
        click = 0.45 * math.exp(-t * 160.0) if i < int(0.03 * SAMPLE_RATE) else 0.0
        add_sample(buffer, start + i, (math.sin(phase) * 0.95 + click) * amp)


def synth_snare(buffer, start):
    length = int(0.22 * SAMPLE_RATE)
    for i in range(length):
        t = i / SAMPLE_RATE
        noise_env = math.exp(-t * 20.0)
        tone_env = math.exp(-t * 28.0)
        noise = random.uniform(-1.0, 1.0) * noise_env * 0.65
        tone = math.sin(2.0 * math.pi * 185.0 * t) * tone_env * 0.35
        add_sample(buffer, start + i, noise + tone)


def synth_hihat(buffer, start):
    length = int(0.075 * SAMPLE_RATE)
    for i in range(length):
        t = i / SAMPLE_RATE
        env = math.exp(-t * 65.0)
        noise = random.uniform(-1.0, 1.0)
        shimmer = math.sin(2.0 * math.pi * 8200.0 * t) * 0.22
        add_sample(buffer, start + i, (noise * 0.45 + shimmer) * env)


def write_wav(path, bpm, bars, kick_steps):
    random.seed(13)
    beats = bars * 4
    seconds_per_beat = 60.0 / bpm
    total_samples = int((beats * seconds_per_beat + 0.75) * SAMPLE_RATE)
    buffer = [0.0] * total_samples

    for bar in range(bars):
        bar_offset = bar * 4.0
        for step in range(8):
            beat_offset = bar_offset + step * 0.5
            index = int(beat_offset * seconds_per_beat * SAMPLE_RATE)
            synth_hihat(buffer, index)

        for beat in (2, 4):
            beat_offset = bar_offset + (beat - 1)
            index = int(beat_offset * seconds_per_beat * SAMPLE_RATE)
            synth_snare(buffer, index)

        for step in kick_steps:
            beat_offset = bar_offset + step * 0.5
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


def write_midi(path, bpm, bars, kick_steps):
    events = bytearray()
    tempo = int(60_000_000 / bpm)
    events.extend(b"\x00\xff\x51\x03" + tempo.to_bytes(3, "big"))
    events.extend(b"\x00\xff\x58\x04\x04\x02\x18\x08")

    notes = []
    for bar in range(bars):
        base = bar * 4 * PPQ
        for step in range(8):
            notes.append((base + step * PPQ // 2, 42, 62, PPQ // 8))
        for beat in (2, 4):
            notes.append((base + (beat - 1) * PPQ, 38, 92, PPQ // 4))
        for step in kick_steps:
            notes.append((base + step * PPQ // 2, 36, 108, PPQ // 4))

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
    if len(sys.argv) != 6:
        print("usage: generate_drum_sample.py BPM BARS KICK_STEPS_CSV WAV_PATH MIDI_PATH", file=sys.stderr)
        return 2

    bpm = int(sys.argv[1])
    bars = int(sys.argv[2])
    kick_steps = [int(step) for step in sys.argv[3].split(",") if step]
    wav_path = Path(sys.argv[4])
    midi_path = Path(sys.argv[5])

    write_wav(wav_path, bpm, bars, kick_steps)
    write_midi(midi_path, bpm, bars, kick_steps)
    print(f"wrote {wav_path}")
    print(f"wrote {midi_path}")


if __name__ == "__main__":
    raise SystemExit(main())
