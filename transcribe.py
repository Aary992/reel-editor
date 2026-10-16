import json, sys, time
from faster_whisper import WhisperModel
t = time.time()
m = WhisperModel("small", device="cpu", compute_type="int8")
segs, info = m.transcribe(sys.argv[1], word_timestamps=True, vad_filter=False, condition_on_previous_text=False)
words = [{"w": w.word, "s": round(w.start, 3), "e": round(w.end, 3), "p": round(w.probability, 2)} for s in segs for w in s.words]
json.dump({"lang": info.language, "lang_p": info.language_probability, "words": words}, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(f"lang={info.language} p={info.language_probability:.2f}  {len(words)} words in {time.time()-t:.1f}s")
print("".join(x["w"] for x in words))
low = [x for x in words if x["p"] < 0.5]
print("low-confidence:", ", ".join(f'{x["w"].strip()}({x["p"]})@{x["s"]}' for x in low))
