# BGM音源フォルダ

ここに置いた音源ファイル(mp3 / m4a / wav / aac / ogg)が、Instagramリールの BGM として
日付でローテーション使用されます(ファイル名の昇順で並べ、日付の連番を3で割った余りで選ばれます)。

## 使い方

1. 著作権フリー(商用利用・改変・第三者への公開が許可されているもの)の音源を3つ用意する
2. このフォルダに置く(ファイル名は自由。例: `track1.mp3` `track2.mp3` `track3.mp3`)
3. `git add automation/music/*.mp3` → `git commit` → `git push` で**必ずリポジトリにコミットする**

> ⚠ **重要**: 自動投稿はあなたのPCではなくGitHub Actions(クラウド)上で実行されます。
> このフォルダにファイルを置くだけでPC上に保存しても、gitで commit & push しないと
> クラウド側からは見えません。置いたら必ずpushしてください。

## ファイルが無い場合

このフォルダに対象拡張子のファイルが1つもない場合、`reels_media.py` が自動的に
ffmpegで合成したアンビエント音(著作権フリー、実在の楽曲ではない)にフォールバックします。
エラーにはならず、実行ログに `⚠ automation/music/ に音源ファイルが見つからないため...` と出力されます。

## ライセンスについて

生成されたリール動画は**Instagramで一般公開**されます。以下のような、商用・二次配布利用が
明確に許可されている音源を選んでください(いずれも無料で使える楽曲を配布しているサイトです)。

- YouTube Audio Library (https://www.youtube.com/audiolibrary)
- Pixabay Music (https://pixabay.com/music/)
- Chosic (https://www.chosic.com/free-music/)
- Uppbeat (https://uppbeat.io/)

サイトごとにクレジット表記が必要な場合があるので、ダウンロード時に表示されるライセンス条件を確認してください。
