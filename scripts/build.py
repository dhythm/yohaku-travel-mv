"""Rebuild the approved 60-second film using only this repository's inputs."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'build/yohaku-travel-final.mp4')
    parser.add_argument('--ffmpeg',default=shutil.which('ffmpeg'))
    parser.add_argument('--ffprobe',default=shutil.which('ffprobe'))
    parser.add_argument('--skip-asset-check',action='store_true',help='Allow intentionally edited assets.')
    args=parser.parse_args()
    if not args.ffmpeg or not args.ffprobe:parser.error('Install FFmpeg with libx264 and put ffmpeg/ffprobe on PATH.')
    project=json.loads((ROOT/'project/timeline.json').read_text());timeline=project['timeline']
    if not args.skip_asset_check:
        for item in json.loads((ROOT/'project/assets.json').read_text()):
            path=ROOT/item['file']
            if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:raise RuntimeError(f'Asset missing or changed: {item["file"]}')
    assert all(a['end']==b['start'] for a,b in zip(timeline,timeline[1:]))
    assert timeline[0]['start']==0 and timeline[-1]['end']==project['duration']
    args.output=args.output.resolve();args.output.parent.mkdir(parents=True,exist_ok=True)
    ff=args.ffmpeg;fp=args.ffprobe;fps=project['fps'];width,height=project['canvas'];paper='0xfaf6ec'
    def run(command):subprocess.run(command,check=True)
    def image_input(cmd,path):cmd.extend(['-loop','1','-framerate',str(fps),'-i',str(path)])
    def video(cid):return ROOT/project['videos'][cid]['file']
    def graphic(name):return ROOT/(project['graphics'].get(name) or project['static_type'][name])
    with tempfile.TemporaryDirectory(prefix='render-',dir=args.output.parent) as temp:
        work=Path(temp);audio=work/'audio'
        run([sys.executable,str(ROOT/'scripts/score.py'),str(audio)])
        run([sys.executable,str(ROOT/'scripts/atmosphere.py'),str(audio)])
        segments=[]
        for scene in timeline:
            duration=scene['end']-scene['start'];frames=round(duration*fps);mode=scene.get('mode','full')
            cmd=[ff,'-hide_banner','-loglevel','error','-y'];filters=[];inputs=0
            if mode=='door_edit':
                cmd+=['-ss','0.25','-i',str(video('V02')),'-ss','0.5','-i',str(video('V07')),'-ss','5','-i',str(video('V02'))];inputs=3
                for j,seconds in enumerate([2.75,1.25,3]):filters.append(f'[{j}:v]fps=24,trim=duration={seconds},scale=1080:1920:flags=lanczos,setsar=1,setpts=PTS-STARTPTS,format=yuv420p[p{j}]')
                filters.append('[p0][p1][p2]concat=n=3:v=1:a=0[base]')
            elif mode=='end':
                cmd+=['-i',str(video('V07')),'-i',str(video('V08'))];image_input(cmd,graphic('end_bg'));inputs=3
                filters+=['[0:v]setpts=1.5*(PTS-STARTPTS),fps=24,scale=452:800:force_original_aspect_ratio=increase,crop=452:800,setsar=1[left]','[1:v]setpts=1.5*(PTS-STARTPTS),fps=24,scale=452:800:force_original_aspect_ratio=increase,crop=452:800,setsar=1[right]','[2:v]format=rgba,setpts=PTS-STARTPTS[paper]','[paper][left]overlay=72:72:shortest=1[one]','[one][right]overlay=556:72:shortest=1[base]']
            elif mode in ['card','tag']:
                image_input(cmd,graphic(scene['base']));inputs=1;filters.append('[0:v]format=rgba,setpts=PTS-STARTPTS[base]')
                if mode=='tag':
                    image_input(cmd,ROOT/project['stills']['13_coffee_detail']);inputs+=1
                    filters+=['[1:v]scale=920:750:force_original_aspect_ratio=increase,crop=920:750:0:ih-750-70,setsar=1[photo]','[base][photo]overlay=80:1090[insert]']
            else:
                if scene.get('clip'):cmd+=['-ss',str(round(scene['offset']*fps)/fps),'-i',str(video(scene['clip']))]
                else:image_input(cmd,ROOT/project['stills'][scene['image']])
                inputs=1
                if mode=='stay':filters+=['[0:v]fps=24,scale=1080:1240:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1240,setsar=1,setpts=PTS-STARTPTS[photo]',f'color=c={paper}:s=1080x1920:r=24:d={duration}[paper]','[paper][photo]overlay=0:0:shortest=1[base]']
                else:
                    zoom=scene.get('zoom',1);ww=int(width*zoom)//2*2;hh=int(height*zoom)//2*2
                    vf=f'[0:v]fps=24,scale={ww}:{hh}:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,setsar=1,setpts=PTS-STARTPTS'
                    if scene.get('fade_in'):vf+=f',fade=t=in:d={scene["fade_in"]}:color={paper}'
                    filters.append(vf+'[base]')
            current='insert' if mode=='tag' else 'base'
            if scene.get('bg'):
                image_input(cmd,graphic(scene['bg']));idx=inputs;inputs+=1
                filters+=[f'[{idx}:v]format=rgba,setpts=PTS-STARTPTS[bg]',f'[{current}][bg]overlay=0:0:shortest=1:format=auto[withbg]'];current='withbg'
            if scene.get('type'):
                asset=scene['type']
                if asset in project['motion']:
                    plan=project['motion'][asset];image_input(cmd,ROOT/plan['base']);idx=inputs;inputs+=1
                    filters+=[f'[{idx}:v]format=rgba,setpts=PTS-STARTPTS[jpbase]',f'[{current}][jpbase]overlay=0:0:shortest=1:format=auto[jpunder]'];current='jpunder'
                    for j,part in enumerate(plan['parts']):
                        image_input(cmd,ROOT/part['file']);idx=inputs;inputs+=1
                        st=part['start'];fade=part['fade_seconds'];rise=part['rise_pixels']
                        vf=f'[{idx}:v]format=rgba,setpts=PTS-STARTPTS,fade=t=in:st={st}:d={fade}:alpha=1'
                        if scene.get('type_out'):vf+=f',fade=t=out:st={scene["type_out"]-.4}:d=0.4:alpha=1'
                        filters.append(vf+f'[jp{j}]');y=f"'{part['y']}+{rise}*pow(max(0\\,1-max(0\\,t-{st})/{fade})\\,3)'"
                        filters.append(f'[{current}][jp{j}]overlay={part["x"]}:{y}:shortest=1:format=auto[jpc{j}]');current=f'jpc{j}'
                else:
                    image_input(cmd,graphic(asset));idx=inputs;inputs+=1
                    filters+=[f'[{idx}:v]format=rgba,setpts=PTS-STARTPTS[type]',f'[{current}][type]overlay=0:0:shortest=1:format=auto[composed]'];current='composed'
            filters.append(f'[{current}]format=yuv420p[v]');destination=work/(scene['id']+'.mp4');segments.append(destination)
            print(f'{scene["id"]}/15 {scene["label"]}',flush=True)
            run(cmd+['-filter_complex',';'.join(filters),'-map','[v]','-an','-frames:v',str(frames),'-c:v','libx264','-preset','fast','-crf','18','-r','24','-video_track_timescale','24000','-movflags','+faststart',str(destination)])
        listing=work/'concat.txt';listing.write_text(''.join("file '"+str(p).replace("'","'\\''")+"'\n" for p in segments))
        picture=work/'picture.mp4';run([ff,'-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(listing),'-c','copy','-movflags','+faststart',str(picture)])
        # Match the approved picture pipeline before the bitrate-limited encode.
        master=work/'picture-master.mp4';color=['-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-color_range','tv']
        run([ff,'-hide_banner','-loglevel','error','-y','-i',str(picture),'-an','-c:v','libx264','-profile:v','high','-level:v','4.1','-preset','slow','-crf','18','-pix_fmt','yuv420p','-r','24','-video_track_timescale','24000',*color,'-movflags','+faststart',str(master)])
        print('25MB以下の映像を作成',flush=True)
        base=[ff,'-hide_banner','-loglevel','error','-y','-i',str(master),'-map','0:v:0','-c:v','libx264','-preset','slow','-b:v',project['delivery']['video_bitrate'],'-pix_fmt','yuv420p','-profile:v','high','-level:v','4.1','-r','24','-frames:v',str(round(project['duration']*fps)),'-passlogfile',str(work/'bitrate')]
        run(base+['-pass','1','-an','-f','null',str(Path('/dev/null'))] if sys.platform!='win32' else base+['-pass','1','-an','-f','null','NUL'])
        compressed=work/'compressed-picture.mp4';run(base+['-pass','2','-an','-video_track_timescale','24000',*color,'-movflags','+faststart',str(compressed)])
        final=work/'final.mp4';run([ff,'-hide_banner','-loglevel','error','-y','-i',str(compressed),'-i',str(audio/'temp-score-and-atmosphere.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-af','loudnorm='+project['audio']['loudnorm'],'-t',str(project['duration']),'-movflags','+faststart',str(final)])
        metadata=json.loads(subprocess.check_output([fp,'-v','error','-show_format','-show_streams','-of','json',str(final)]));v=next(s for s in metadata['streams'] if s['codec_type']=='video');a=next(s for s in metadata['streams'] if s['codec_type']=='audio')
        assert int(v['nb_frames'])==1440 and (v['width'],v['height'])==(width,height) and abs(float(metadata['format']['duration'])-60)<.03
        assert a['sample_rate']=='48000' and a['channels']==2
        assert final.stat().st_size<project['delivery']['maximum_bytes'],final.stat().st_size
        run([ff,'-hide_banner','-loglevel','error','-err_detect','explode','-i',str(final),'-f','null','-'])
        shutil.move(str(final),str(args.output))
    report={'file':str(args.output),'bytes':args.output.stat().st_size,'frames':1440,'duration_seconds':60,'canvas':[width,height],'full_decode':'passed','sha256':hashlib.sha256(args.output.read_bytes()).hexdigest(),'ffmpeg_version':subprocess.check_output([ff,'-version']).decode().splitlines()[0]}
    args.output.with_suffix('.checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
