from pathlib import Path
import json, wave
import numpy as np

import argparse
parser=argparse.ArgumentParser();parser.add_argument('output_directory',type=Path);args=parser.parse_args()
OUT=args.output_directory;OUT.mkdir(parents=True,exist_ok=True)
SR=48000;DUR=60
audio=np.zeros((SR*DUR,2),dtype=np.float64)
rng=np.random.default_rng(20261004)
def hz(m):return 440*2**((m-69)/12)
def add_note(start,midi,length=2.4,level=.10,pan=.5):
    count=min(int(length*SR),len(audio)-int(start*SR))
    if count<=0:return
    t=np.arange(count)/SR
    f=hz(midi)
    attack=1-np.exp(-t/.009)
    decay=np.exp(-t/(.75 if midi>65 else 1.3))
    ending=np.minimum(1,np.maximum(0,(length-t)/.16))
    tone=(np.sin(2*np.pi*f*t)+.25*np.sin(2*np.pi*2*f*t)*np.exp(-t/0.45)+.10*np.sin(2*np.pi*3*f*t)*np.exp(-t/.22))
    tone*=attack*decay*ending*level
    offset=int(start*SR)
    audio[offset:offset+count,0]+=tone*np.sqrt(1-pan)
    audio[offset:offset+count,1]+=tone*np.sqrt(pan)
    # A restrained, short stereo echo softens the synthetic pluck.
    for delay,gain in [(.12,.10),(.25,.055)]:
        off=offset+int(delay*SR);n=min(count,len(audio)-off)
        audio[off:off+n,0]+=tone[:n]*gain*np.sqrt(pan)
        audio[off:off+n,1]+=tone[:n]*gain*np.sqrt(1-pan)
chords=[[50,57,61,66,69],[45,52,57,61,64],[47,54,57,62,66],[43,50,57,59,62]]
beat=60/84
for bar in range(19):
    start=10+bar*beat*4
    if start>=57:break
    chord=chords[bar%4]
    quiet=1  # Consistent arrangement gain through the 35-second title card.
    add_note(start,chord[0],3,.095*quiet,.45)
    for k,n in enumerate(chord[1:]):
        when=start+k*beat
        add_note(when,n+12,2.1,.07*quiet,.3+.15*(k%3))
    if start<35 or start>=48:
        add_note(start+beat*1.5,chord[2]+24,1.4,.032*quiet,.72)
        add_note(start+beat*3.5,chord[3]+12,1.7,.038*quiet,.28)
for start,n in [(0.3,50),(2.8,57),(5.0,61),(8.5,69),(55.0,50),(55.08,57),(55.16,61),(55.24,66),(55.32,69)]:
    add_note(start,n,4,.055 if start<10 else .075,.5)
# Low-density sustained harmony; no purchased or copied samples are used.
for bar in range(7):
    start=10+bar*beat*8
    if start>=58:break
    chord=chords[(bar*2)%4]
    count=min(int(beat*8*SR),len(audio)-int(start*SR))
    t=np.arange(count)/SR;env=np.sin(np.pi*np.minimum(t/(beat*8),1))**1.4
    for k,n in enumerate(chord[1:4]):
        sig=(np.sin(2*np.pi*hz(n)*t)+.3*np.sin(2*np.pi*hz(n)*1.0015*t))*env*.012
        off=int(start*SR)
        audio[off:off+count,k%2]+=sig
        audio[off:off+count,1-k%2]+=sig*.65
time=np.arange(len(audio))/SR
gain=np.minimum(1,time/.7)*np.minimum(1,np.maximum(0,(60-time)/3))
# No hard section-level gain switches; they create audible discontinuities.
audio*=gain[:,None]
peak=float(np.max(np.abs(audio)))
audio*=min(1,.50/max(peak,1e-9))
pcm=np.int16(np.clip(audio,-1,1)*32767)
path=OUT/'original-temp-score.wav'
with wave.open(str(path),'wb') as f:
    f.setnchannels(2);f.setsampwidth(2);f.setframerate(SR);f.writeframes(pcm.tobytes())
(OUT/'score_notes.json').write_text(json.dumps({'type':'original procedural temporary score','tempo':84,'duration':60,'sample_rate':SR,'peak_dbfs':round(20*np.log10(np.max(np.abs(audio))),2),'note':'独自に合成した仮BGM。完成版の音楽としての聴取審査は未実施。'},ensure_ascii=False,indent=2))
print('Created a 60-second original temporary score.')
