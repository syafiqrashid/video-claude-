import sys, types
m = types.ModuleType("torchaudio.backend.common")
class AudioMetaData: pass
m.AudioMetaData = AudioMetaData
sys.modules["torchaudio.backend"] = types.ModuleType("torchaudio.backend"); sys.modules["torchaudio.backend.common"] = m
import numpy as np, soundfile as sf, torch
from df.enhance import init_df, enhance
import os; model, state, _ = init_df(model_base_dir=os.environ["DF_MODEL"])
x, sr = sf.read(sys.argv[1], dtype="float32")
assert sr == state.sr(), (sr, state.sr())
x = x if x.ndim == 1 else x.mean(1)
atten = float(sys.argv[3]) if len(sys.argv) > 3 else None
y = enhance(model, state, torch.from_numpy(x)[None], atten_lim_db=atten)
sf.write(sys.argv[2], y[0].numpy(), sr)
print("ok", sys.argv[2])
