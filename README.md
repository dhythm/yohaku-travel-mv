# 余白旅行 — 60秒広告

日本語の文字演出、海と森の映像、紙飛行機のシンボルを組み合わせた架空の旅行会社の広告です。承認済みの映像と、35秒付近の音量変化・クリックを修正した音声を保存しています。

## 最終版

[動画を開く](dist/yohaku-travel-final.mp4) ／ [ブラウザで確認する](index.html)

60秒・1080×1920・24fps。H.264／AAC、24,333,801 bytes（24.33 MB）。25 MB は 25,000,000 bytes として確認しています。

## 保存内容

- `dist/`：最終版1本。
- `assets/video/`：採用動画8本。元のファイル名との対応は `project/timeline.json`。
- `assets/stills/`：採用写真2枚。
- `assets/graphics/`：使用する背景・文字のPNG、文字の分割レイヤー、編集用SVG。
- `project/timeline.json`：カット位置、画像・文字の配置、文字の出現時間、出力設定。
- `project/assets.json`：すべての素材のサイズとSHA-256。
- `scripts/`：映像の組み立て、音楽・環境音の生成、圧縮・検証。
- `docs/`：制作工程、採用素材の生成指示の記録。

不採用素材、旧版、書き出し途中の動画、試聴用音声、検証画像は保存しません。素材と最終版を通常のGitで管理します。Git LFSや外部素材のダウンロードは不要です。

## クローンから再作成

Python 3.11以上と、libx264を含むFFmpeg／ffprobeを用意してください。検証環境はPython 3.12.14、NumPy 2.3.5、FFmpeg 9.0.2です。macOSではFFmpegを `brew install ffmpeg` で導入できます。

リポジトリのルートで実行します。

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/build.py
```

Windowsでは仮想環境の有効化に `.venv\Scripts\Activate.ps1` を使用します。

完成動画は `build/yohaku-travel-final.mp4`、検証結果は `build/yohaku-travel-final.checks.json` に出力されます。途中の映像・音声は一時領域で作成して自動削除し、`build/` と `.venv/` はGit対象外です。作業用の空き容量は1 GB以上を目安にしてください。

文字の確定PNGを使うため、再作成にヒラギノフォントや生成AIサービスへのログインは不要です。音声も保存されたコードから生成します。FFmpegの場所を指定する場合は `--ffmpeg /path/to/ffmpeg --ffprobe /path/to/ffprobe` を使用できます。

保存素材のハッシュを確認した後、全15シーン、音響、圧縮を実行します。60秒・1440フレーム・画面サイズ・音声形式・25 MB未満・全編のデコードを自動確認します。クローンから実際に再作成し、承認済みファイルとのSHA-256の完全一致を確認しました。結果は `project/rebuild-verification.json` に記録しています。エンコーダーやライブラリのバージョンによって、再書き出しの圧縮結果やファイルのハッシュは変わる場合があります。

## 編集する場合

映像の差し替えや時間・配置変更は `project/timeline.json` と対応素材を編集します。意図的に素材を変更した際はハッシュも更新するか、`python scripts/build.py --skip-asset-check` を使用してください。

SVGは文字・配色・シンボルの編集元です。SVGの編集内容は自動でPNGへ反映されません。文字を編集する場合は、ヒラギノ角ゴシックを使える環境でSVGを再描画し、対応する背景・文字レイヤーPNGを更新してください。分割PNGの座標・寸法・アニメーション開始時間は `project/timeline.json` の `motion` にあります。既存の見た目を再作成する場合、この操作は不要です。

詳しい工程は [制作記録](docs/production.md) を参照してください。
