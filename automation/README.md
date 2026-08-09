# 本質のAI活用術 自動化(claude.ai/code routines版)

**claude.ai/code の「routines」(スケジュール済みクラウドエージェント)** 上で動きます。
PCの電源が入っていなくても実行され、Anthropic APIやOpenAI APIの従量課金は一切発生しません
(Claude Proのサブスクリプション契約の範囲内で実行されます)。

## 何をするか

| routine | 内容 | 投稿・送信先 | 実行タイミング(JST) |
|---|---|---|---|
| 朝の単発ポスト | Claude自身がWeb検索でAI活用インフルエンサーの傾向を調べ、単発ポストを生成し、**XとThreadsに自動投稿**する | X・Threadsに自動投稿 + 結果報告メール | 毎日 8:07 |
| お昼のスレッド | 同様にリサーチし、5投稿構成のスレッドを生成して**XとThreadsに自動投稿**する | X・Threadsに自動投稿 + 結果報告メール | 毎日 12:12 |
| 夜の単発ポスト | 朝とは型をずらした単発ポストを生成して**XとThreadsに自動投稿**する | X・Threadsに自動投稿 + 結果報告メール | 毎日 20:20 |
| 週次note下書き | 似た発信者をリサーチし、まだ扱っていない新テーマを自分で提案してnote新作(企画〜集客文まで)を作成。扱ったテーマは `themes_log.json` に記録し、二度と同じテーマを提案しない | メール(下書き、要手動投稿) | 毎週月曜 9:15 |
| Instagramリール | Canva/Gamma連携で画像を生成し、ffmpegでKen Burns風にアニメーション化+ローテーションBGMを乗せた縦型動画+キャプションを作成し、**Instagramに自動投稿**する | Instagramに自動投稿 + 結果報告メール | 毎日 8:03 |

> ⚠ **SNS(X・Threads・Instagram)の4本は完全自動投稿です。** 人の確認を挟まず、生成された内容がそのまま公開されます。
> noteは引き続き下書きメールのみで、実際の投稿はご自身で行ってください。

## アーキテクチャ(旧GitHub Actions版との違い)

以前はGitHub Actions上のPythonスクリプトがAnthropic API(文章生成・Web検索、従量課金)と
OpenAI API(画像生成、従量課金)を直接呼び出していました。この構成では、それらのAPI呼び出しは
**すべてroutine実行時のClaude自身(Claude Pro契約分)が担当**し、Pythonスクリプトは
「投稿API呼び出し・動画合成・メール送信」といった機械的な処理だけを行います。

具体的には、各routineは以下の流れで動きます:

1. Claude(routineのエージェント自身)が `automation/common.py` の `BRAND_CONTEXT` を読み、
   ブランドの世界観を把握する
2. Claude自身の **WebSearch** ツールでAI活用系の発信トレンドをリサーチする
3. Claude自身の判断で、今回の切り口・投稿文・(Instagramの場合は画像)を作成する
4. 作成した内容を `automation/outputs/*.json` に書き出す
5. `pip install -r automation/requirements.txt` を実行し、`python automation/post_single.py <json>` など
   機械的な投稿スクリプトをBashで実行する(X/Threads/Instagram投稿、動画合成、メール送信はここで行う)

そのため、`content_research.py` / `content_strategist.py` / `sns_single_post.py` / `sns_thread.py` /
`weekly_note.py` / `daily_instagram.py` (いずれも旧・Claude/OpenAI API直接呼び出し版)は廃止し、
代わりに以下の「機械的な実行部分だけ」のスクリプトを追加しています:

- `post_single.py` … 単発ポストのJSONを受け取り、X/Threadsに投稿+結果メール
- `post_thread.py` … スレッドのJSONを受け取り、X/Threadsに投稿+結果メール
- `send_note_draft.py` … note下書きのJSONを受け取り、下書きメール送信+`themes_log.json`更新
- `post_instagram_reel.py` … 生成済み画像+キャプションのJSONを受け取り、ffmpegで動画化して
  公開用リポジトリへpush、Instagramに投稿+結果メール(画像添付)

`social_post.py`(X/Threads投稿)・`instagram_post.py`(Instagram投稿)・`media_repo.py`(動画配信用リポジトリへのpush)・
`reels_media.py`(ffmpegでの動画・BGM合成)は、もともとClaude/OpenAI APIを呼んでいなかったため変更していません。

> 🎵 Instagramリールの背景音楽(BGM)は、以前と同様 `automation/music/` に置いた実在の音源ファイルを
> 日付で3パターンローテーションして使います(未用意の場合はffmpeg合成音にフォールバック)。

## セットアップ手順

### 1. X (旧Twitter) APIキーの取得(自動投稿用)

以前と同じ手順です。投稿先の「サカキ」用Xアカウントでログインした状態で、
https://developer.x.com で開発者アプリを作成し、`X_API_KEY` / `X_API_SECRET` /
`X_ACCESS_TOKEN` / `X_ACCESS_TOKEN_SECRET` を発行してください(App permissionsは
**Read and Write** に設定)。

### 2. Threads APIキーの取得(自動投稿用)

以前と同じ手順です。https://developers.facebook.com でアプリを作成し「Threads API」を追加、
Graph API Explorerでアクセストークンを発行→長期(60日)トークンに交換して
`THREADS_USER_ID` / `THREADS_ACCESS_TOKEN` を控えてください。

> ⚠ 長期トークンは60日で失効します。失効前に交換URLを再実行し、環境変数(下記手順6)を更新してください。

### 3. Instagram APIキーの取得(リール自動投稿用)

以前と同じ手順です。「Instagram API with Instagram Login」方式で `IG_USER_ID` /
`IG_ACCESS_TOKEN`(`IGAA`から始まる)を発行してください。こちらも60日で失効します。

### 4. Gmailアプリパスワードの発行(結果報告メール用)

以前と同じ手順です。goliath24520@gmail.com で2段階認証を有効化し、
https://myaccount.google.com/apppasswords でアプリパスワードを発行してください。

### 5. リール動画配信用のPublicリポジトリとPATを用意する

以前と同じ手順です。動画ファイルだけを置く空のPublicリポジトリ(例:`ai-note-reels-media`)を作成し、
Fine-grained PAT(Contents: Read and write)を発行して `MEDIA_REPO` / `MEDIA_REPO_TOKEN` を控えてください。

### 6. claude.ai/code の「環境(Environment)」に環境変数を登録する

このリポジトリには `.env` を置きません(routineはクラウド上の独立したセッションで動くため、
ローカルの `.env` は読み込まれません)。代わりに、routineが使う **claude.ai/code の環境(Environment)** に
環境変数として登録します。5本のroutineはすべて環境名「note2」(environment_id: `env_019EJkPYpJqspyTtZGGE5GV4`)を
使う設定になっています(2026年8月時点で確認済み。以前の「Default」から変更しました)。

> ⚠ **重要な注意点**: 下記の環境変数の入力欄には、Anthropic自身が
> 「この環境を使用するすべてのユーザーに表示されるため、シークレットや認証情報は追加しないでください」
> という警告を出しています。2026年8月時点、claude.ai/codeにはこれとは別の暗号化されたシークレット専用の
> 保管場所は用意されていません。そのため、この欄にAPIキーを直接貼り付けることになります。
> **この環境(note2)を他の人と共有・招待しない限り実質的なリスクは低い**ですが、
> 将来誰かとこの環境を共有する場合は、先に値を再発行してから招待するようにしてください。

**登録手順:**

1. https://claude.ai/code を開く(routine一覧ではなく、通常のCode画面でよい)
2. 画面下部の入力欄の左にある実行環境チップ(例:「note2」や環境名が表示されているボタン)をクリックする
3. 表示されたメニューから「クラウド」にカーソルを合わせ、右に出るサブメニューで **「note2」にマウスを重ねると右側に歯車(⚙)アイコンが出る** ので、それをクリックする
   (「note2」がまだ選ばれていない場合は、先に一度クリックして選択してから、もう一度チップをクリックしてメニューを開き直すと歯車が出ます)
4. 「クラウド環境を更新」というダイアログが開く。「環境変数」欄に、以下を **`.env`形式(1行に`KEY=値`)** でそのまま貼り付ける:

```
GMAIL_ADDRESS=goliath24520@gmail.com
GMAIL_APP_PASSWORD=(16桁のアプリパスワード)
MAIL_TO=reon24520@gmail.com
X_API_KEY=(XのAPI Key)
X_API_SECRET=(XのAPI Key Secret)
X_ACCESS_TOKEN=(XのAccess Token)
X_ACCESS_TOKEN_SECRET=(XのAccess Token Secret)
THREADS_USER_ID=(ThreadsユーザーID)
THREADS_ACCESS_TOKEN=(Threads長期アクセストークン)
IG_USER_ID=(Instagram User ID)
IG_ACCESS_TOKEN=(Instagram長期アクセストークン、IGAAから始まる)
MEDIA_REPO=あなたのGitHubユーザー名/ai-note-reels-media
MEDIA_REPO_TOKEN=(手順5で発行したFine-grained PAT、github_pat_から始まる)
```

5. 右下の「変更を保存」をクリックする
6. 「ネットワークアクセス」は初期値の **Trusted** のままでよい(X/Threads/InstagramのAPIや外部サイトへの
   アクセスに必要)

> `ANTHROPIC_API_KEY` と `OPENAI_API_KEY` はもう不要です(登録しないでください)。
> Threads・Instagramのアクセストークンを再発行したときも、同じ画面から値を書き換えて保存してください。

### 7. Canva / Gammaとの連携を確認する(Instagramリールの画像生成用)

Instagramリールの画像は、Claude自身がCanva/Gamma連携(MCP)を使って生成します。
https://claude.ai/customize/connectors で Canva・Gamma が接続済みであることを確認してください。

> ⚠ Canva/Gammaは無料プランの範囲内で使う想定ですが、生成頻度や機能によっては
> 無料枠を超えて別途課金が発生する可能性があります。しばらく運用したら、
> Canva・Gammaそれぞれの利用状況(ダッシュボード)を確認することをおすすめします。

### 8. routineを作成する

このリポジトリ(`rhythme-sns/AI-note-hannbai`)を対象に、上記5本のroutineを
https://claude.ai/code/routines で作成します(Claude Codeに「routineを作って」と依頼すれば
自動で設定できます)。各routineには、投稿する内容の作り方・投稿の仕方・ブランドの制約を
書いた自己完結型のプロンプトが設定されます。

### 9. 動作確認

各routineの「Run Now」で手動実行できます。`DRY_RUN=true` 相当の確認をしたい場合は、
プロンプトに「今回はdry runとして、実際の投稿はスキップし、生成内容をメールで報告するだけにして」
のように一時的に指示するか、routineのプロンプト自体に dry run 手順を組み込んで運用してください。

数十秒〜数分後に結果報告メールが届けば成功です。失敗した場合は
https://claude.ai/code/routines の実行履歴からログを確認できます。

---

## テーマの拡張について

週次note下書きroutineは、固定リストではなく毎回Claude自身がWeb検索で他のAI活用系インフルエンサーの
発信傾向を調べ、`themes_log.json` に記録済みの過去テーマと重複しない新テーマを提案してから執筆します。
routine実行のたびに `themes_log.json` の更新をコミット・pushするよう指示しているため、
手動で編集する必要はありません。

---

## 既知の制約・注意点

- **SNS系の4つは完全自動投稿です。** 生成内容に誤りや不適切な表現があっても、そのまま公開されます。
  結果報告メールで事後確認する運用になるため、違和感のある投稿があれば都度手動で削除・修正してください
- **Threads・Instagramの長期アクセストークンはどちらも60日で失効します。** 失効後は再発行して
  claude.ai/code側の環境変数を更新する必要があります
- **X APIの無料プランには月間投稿数の上限があります。** developer.x.comのダッシュボードで確認してください
- **routineのクラウドサンドボックスにffmpegやpipパッケージが未インストールの場合、
  routine実行時に自動でインストールを試みる**構成にしていますが、サンドボックスの制約で
  失敗する可能性があります。失敗した場合は実行ログを確認してください
- **Canva/Gamma連携の無料枠を超えると、Claude Pro以外の課金が発生する可能性があります。** 定期的に
  それぞれのダッシュボードで利用状況を確認してください
- **リール動画は `MEDIA_REPO` で指定したPublicリポジトリに一時的に公開されます。** 投稿のたびに古い動画は
  削除して1本だけ残す運用ですが、その動画の中身(生成画像・BGM)は誰でも閲覧・ダウンロードできる状態になります
- noteの下書きは、事実確認・表現チェックをしたうえで手動投稿してください(こちらは自動投稿しません)
