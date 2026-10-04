from pathlib import Path
import wave, json, argparse
import numpy as np

parser=argparse.ArgumentParser();parser.add_argument('output_directory',type=Path);args=parser.parse_args()
OUT=args.output_directory;OUT.mkdir(parents=True,exist_ok=True)
with wave.open(str(OUT/'original-temp-score.wav'),'rb') as f:
    sr=f.getframerate();count=f.getnframes()
    audio=np.frombuffer(f.readframes(count),dtype=np.int16).reshape(-1,2).astype(float)/32767
t=np.arange(count)/sr;rng=np.random.default_rng(7404)
def envelope(start,end,fade=1):
    return np.minimum(1,np.maximum(0,(t-start)/fade))*np.minimum(1,np.maximum(0,(end-t)/fade))
# Designed sound cues, explicitly temporary; no generated clip audio is used.
for start in [.6,1.6,2.6,3.6,4.6,5.6]:
    n=int(.07*sr);tt=np.arange(n)/sr
    sig=(np.sin(2*np.pi*1800*tt)+.25*np.sin(2*np.pi*2800*tt))*np.exp(-tt/.006)*.030
    i=int(start*sr);audio[i:i+n,:]+=sig[:,None]
for channel in [0,1]:
    noise=rng.normal(0,1,count)
    low=np.convolve(noise,np.ones(70)/70,mode='same')
    mid=np.convolve(noise,np.ones(12)/12,mode='same')
    surf=(low*.6+mid*.20)
    swell=.65+.35*np.sin(2*np.pi*t/4.8+channel*.22)
    env=envelope(13,23,.7)+envelope(38.8,48,1.1)+envelope(54,60,1.7)
    audio[:,channel]+=surf*swell*env*.038
    leaf=np.convolve(noise,np.ones(8)/8,mode='same')-np.convolve(noise,np.ones(60)/60,mode='same')
    audio[:,channel]+=leaf*envelope(27,31,.6)*.008
audio*=np.minimum(1,np.maximum(0,(60-t)/1.8))[:,None]
peak=float(np.max(np.abs(audio)));assert peak<.9
with wave.open(str(OUT/'temp-score-and-atmosphere.wav'),'wb') as f:
    f.setnchannels(2);f.setsampwidth(2);f.setframerate(sr);f.writeframes(np.int16(audio*32767).tobytes())
(OUT/'sound_notes.json').write_text(json.dumps({'score':'独自に合成した仮BGM','designed_cues':['冒頭の時計','海のノイズのうねり','森の弱い空気音'],'peak_dbfs':round(20*np.log10(peak),2),'listening_review':'未実施。合成した仮音響であり、録音した実際の波音ではない。完成版には音楽・音響の聴取確認が必要。'},ensure_ascii=False,indent=2))
print('Built temporary score with designed clock and environmental cues; no clipping.')
