"""Transcribe one clip stretch by stretch (EXPERIMENT, used by lab/assemble.py; runs in the Whisper venv).

Whisper silently drops repeated words: "I pitched my... [pause] I pitched my startup" came back as one
"my" lasting 3.8 s. Transcribing each stretch of speech on its own (split at pauses) keeps every take.

  python transcribe_chunks.py audio16k.wav chunks.json out.json     (chunks: [[start, end], ...] in seconds)
"""
import json, sys, time, wave
import numpy as np
from faster_whisper import WhisperModel

t0 = time.time()
with wave.open(sys.argv[1], "rb") as w:
    sr = w.getframerate()
    audio = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
chunks = json.load(open(sys.argv[2]))
model = WhisperModel("small", device="cpu", compute_type="int8")
words, lang = [], None
for s, e in chunks:
    piece = audio[int(s * sr): int(e * sr)]
    if len(piece) < sr * 0.2:
        continue
    segs, info = model.transcribe(piece, word_timestamps=True, vad_filter=False, condition_on_previous_text=False,
                                  language=lang)
    lang = lang or info.language          # the first stretch decides the language for the rest
    for sg in segs:
        for x in sg.words:
            words.append({"w": x.word, "s": round(s + x.start, 3), "e": round(s + x.end, 3), "p": round(x.probability, 2)})
json.dump({"lang": lang, "chunks": chunks, "words": words}, open(sys.argv[3], "w", encoding="utf-8"),
          ensure_ascii=False, indent=0)
print(f"{len(chunks)} stretches, {len(words)} words in {time.time() - t0:.1f}s")
