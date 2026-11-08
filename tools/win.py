import sys, soundfile as sf
from faster_whisper import WhisperModel
m = WhisperModel("medium", device="cpu", compute_type="int8")
a,sr=sf.read(sys.argv[1],dtype="float32")
for r in sys.argv[2:]:
    s,e=map(float,r.split('-'))
    seg=a[int(s*sr):int(e*sr)]
    segs,_=m.transcribe(seg,language="ms",word_timestamps=True,condition_on_previous_text=False,beam_size=5,temperature=0)
    print(f"== {r}")
    for x in segs:
        print("  "+" ".join(f"{w.word.strip()}({s+w.start:.2f})" for w in x.words))
