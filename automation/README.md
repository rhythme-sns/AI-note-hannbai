# 本質のAI活用術 自動化スクリプト

GitHub Actions(クラウド)上で動くPythonスクリプトです。**PCの電源が入っていなくても実行されます。**
実行ログはGitHubの「Actions」タブでいつでも確認でき、失敗した場合もそこに残ります。

## 何をするか

| スクリプト | 内容 | 投稿・送信先 | 実行タイミング |
|---|---|---|---|
| `sns_single_post.py morning` | Web検索でAI活用インフルエンサーの傾向を調べ、単発ポストを生成し、**XとThreadsに自動投稿**する(朝用) | X・Threadsに自動投稿 + 結果報告メール | 毎日 8:07 JST |
| `sns_thread.py` | 同様にリサーチし、5投稿構成のスレッドを生成して**XとThreadsに自動投稿**する(お昼用) | X・Threadsに自動投稿 + 結果報告メール | 毎日 12:12 JST |
| `sns_single_post.py evening` | 朝とは型をずらした単発ポストを生成して**XとThreadsに自動投稿**する(夜用) | X・Threadsに自動投稿 + 結果報告メール | 毎日 20:20 JST |
| `weekly_note.py` | 似た発信者をリサーチし、まだ扱っていない新テーマを自分で提案してnote新作(企画〜集客文まで)を作成。扱ったテーマは `themes_log.json` に記録し、二度と同じテーマを提案しない | メール(下書き、要手動投稿) | 毎週月曜 9:15 JST |
| `daily_instagram.py` | Instagram用画像(OpenAIで生成、クリエイター/デザイナー風の情景をランダム生成)+キャプションを作成 | メール(下書き、添付ファイルあり、要手動投稿) | 毎日 8:00 JST |

> ⚠ **SNS(X・Threads)の3本(朝の単発/お昼のスレッド/夜の単発)は完全自動投稿です。**人の確認を挟まず、
> 生成された内容がそのままX・Threadsに公開されます。それぞれ独立して実行されるため、朝と夜の単発ポストは
> 内容の切り口をずらして生成し、単純な繰り返しにならないようにしています。
> 実行時刻は、GitHub Actionsで多くのワークフローが集中しがちな「ちょうど◯時」を避け、数分ずらしてあります。
> note・Instagramは引き続き下書きメールのみで、実際の投稿はご自身で行ってください。

---

## セットアップ手順

### 1. Anthropic APIキーの取得(文章生成・Web検索用)

1. https://console.anthropic.com にアクセスし、アカウントを作成(またはログイン)
2. 左メニューの **Billing** から支払い方法(クレジットカード)を登録する
   - 従量課金制です。Claude Sonnet 5を使用し、目安として入力$2〜3/出力$10〜15 per 100万トークン
     (2026年8月時点、intro価格あり)。1回あたり数十円〜百円程度が目安です
3. 左メニューの **API Keys** から「Create Key」を押し、キー(`sk-ant-...`)をコピーする(一度しか表示されません)

### 2. OpenAI APIキーの取得(Instagram画像生成用)

1. https://platform.openai.com にアクセスし、アカウントを作成(またはログイン)
2. **Settings → Billing** で支払い方法を登録し、少額のクレジットを追加する
3. **API keys** から新規キー(`sk-...`)を作成しコピーする

### 3. Gmailアプリパスワードの発行(goliath24520@gmail.comで送信)

1. goliath24520@gmail.com で https://myaccount.google.com/security を開く
2. 「2段階認証」が無効な場合は先に有効化する(アプリパスワードには2段階認証が必須)
3. https://myaccount.google.com/apppasswords を開き、アプリ名(例:「note自動化」)を入力して作成
4. 表示された16桁のパスワード(スペースなしでOK)を控えておく

### 4. X (旧Twitter) APIキーの取得(自動投稿用)

投稿先の「サカキ」用Xアカウントでログインした状態で進めてください。

1. https://developer.x.com にアクセスし、開発者アカウントを申請・作成する
2. 「Projects & Apps」から新しいプロジェクト・アプリを作成する
3. 作成したアプリの **Settings → User authentication settings** を開き、
   - App permissions を **Read and Write** に変更
   - Type of App は「Web App, Automated App or Bot」を選択
   - Callback URI / Website URL は仮で `https://example.com` などを入力(自動投稿だけなら実際に使いません)
4. **Keys and tokens** タブを開き、以下4つを発行・コピーする(権限変更後は再発行が必要です):
   - API Key / API Key Secret
   - Access Token / Access Token Secret(「Generate」ボタンで発行。Read and Write権限になっていることを確認)

> 無料プランでも投稿(POST)は可能ですが、月間投稿数に上限があります。現在の上限は
> developer.x.com のダッシュボードで確認してください。想定投稿数(単発1件+スレッド14件=1日15件、
> X・Threads合計で1日30件×30日=約900件)が上限を超えそうな場合は、有料プランへの変更を検討してください。

### 5. Threads APIキーの取得(自動投稿用)

投稿先の「サカキ」用Threadsアカウント(Instagramと連携したプロフェッショナルアカウントである必要があります)で進めてください。

1. https://developers.facebook.com にアクセスし、開発者アカウントを作成する
2. 「My Apps」から新しいアプリを作成(タイプは「Other」→「Business」などを選択)
3. アプリのダッシュボードで **製品を追加** から「Threads API」を追加する
4. Threads APIの設定画面から、投稿したいThreadsアカウントを連携する
5. **Graph API Explorer**(https://developers.facebook.com/tools/explorer/)を開き、
   作成したアプリを選択→対象のThreadsユーザーとしてアクセストークンを発行する
   (`threads_basic`, `threads_content_publish` の権限を付与)
6. 発行された短期トークンを、長期(60日)トークンに交換する(以下のURLをブラウザで開く。
   `{app-id}` `{app-secret}` `{short-lived-token}` は実際の値に置き換える):
   ```
   https://graph.threads.net/access_token?grant_type=th_exchange_token&client_id={app-id}&client_secret={app-secret}&access_token={short-lived-token}
   ```
   返ってきたJSONの `access_token` が `THREADS_ACCESS_TOKEN` です
7. 投稿対象の `THREADS_USER_ID` は、以下のURLで確認できます:
   ```
   https://graph.threads.net/v1.0/me?fields=id,username&access_token={long-lived-token}
   ```

> ⚠ **長期トークンは60日で失効します。** 失効するとThreads投稿だけがエラーになります(Xやnote/Instagramは影響を受けません)。
> 60日ごとに上記6の交換URLを再度実行してSecretsを更新するか、失効前にリマインダーを設定しておくことをおすすめします。

### 6. GitHubリポジトリを作る

1. https://github.com/new を開く
2. リポジトリ名を決める、**Private** を選択して「Create repository」
3. 作成後に表示されるリモートURLを控えておく

### 7. Secrets(暗号化された環境変数)を登録する

作成したリポジトリの **Settings → Secrets and variables → Actions → New repository secret** から、
以下をそれぞれ登録してください(値は前の手順で控えたもの):

| Secret名 | 値 |
|---|---|
| `ANTHROPIC_API_KEY` | `sk-ant-...` |
| `OPENAI_API_KEY` | `sk-...` |
| `GMAIL_ADDRESS` | `goliath24520@gmail.com` |
| `GMAIL_APP_PASSWORD` | (16桁のアプリパスワード) |
| `MAIL_TO` | `reon24520@gmail.com` |
| `X_API_KEY` | Xの API Key |
| `X_API_SECRET` | Xの API Key Secret |
| `X_ACCESS_TOKEN` | Xの Access Token |
| `X_ACCESS_TOKEN_SECRET` | Xの Access Token Secret |
| `THREADS_USER_ID` | ThreadsユーザーID |
| `THREADS_ACCESS_TOKEN` | Threads長期アクセストークン |

### 8. このフォルダをGitHubにpushする

このプロジェクトフォルダ(`notehannbai2`)のルートで実行してください(すでにpush済みの場合は不要です)。

```bash
cd "C:\Users\reon2\OneDrive\デスクトップ\notehannbai2"
git add .
git commit -m "X/Threads自動投稿対応"
git push
```

`.env` ファイルは `.gitignore` で除外されるため、誤って公開される心配はありません
(APIキーはSecretsにのみ保存されます)。

### 9. 動作確認(手動実行)

GitHubのリポジトリページ → **Actions** タブ → 左側から実行したいワークフロー
(例:「SNS Morning Single Post」)を選び → 右側の「Run workflow」ボタンを押すと、その場ですぐ実行できます。

SNS系の3つ(`SNS Morning Single Post` / `SNS Midday Thread` / `SNS Evening Single Post`)は、
その場でX・Threadsに実際に投稿されます。テスト実行する際はその点に注意してください。
数十秒〜数分後に結果報告メールが届けば成功です。失敗した場合はActionsタブの実行ログに詳細が表示されます。

以降は、設定した時刻に自動で実行されます(PCの電源状態に関係なく動きます)。

---

## テーマの拡張について

`weekly_note.py` は固定リストではなく、毎回Web検索で他のAI活用系インフルエンサーの発信傾向を調べ、
`themes_log.json` に記録済みの過去テーマと重複しない新テーマを自分で提案してから執筆します。
そのため運用を続けるほどテーマの引き出しが自然に広がっていきます。
`themes_log.json` はワークフロー実行のたびに自動更新・コミットされるので、手動で編集する必要はありません。

---

## (オプション)ローカルPCでも動かしたい場合

`run_sns_morning.bat` / `run_sns_thread.bat` / `run_sns_evening.bat` / `run_daily_instagram.bat` / `run_weekly_note.bat` を使えば、
このPC上でも従来通りタスクスケジューラ経由で実行できます。ただしPCの電源が入っている必要があるため、
基本的にはGitHub Actions側の実行のみで十分です。ローカル実行する場合は `.env` ファイルを
`.env.example` を元に作成してください。

---

## 既知の制約・注意点

- **SNS系の3つ(朝の単発/お昼のスレッド/夜の単発)は完全自動投稿です。** 生成内容に誤りや不適切な表現があっても、
  そのまま公開されます。結果報告メールで事後確認する運用になるため、違和感のある投稿があれば都度手動で削除・修正してください
- **Threadsの長期アクセストークンは60日で失効します。** 失効後は再発行してSecretsを更新する必要があります
- **X APIの無料プランには月間投稿数の上限があります。** 想定投稿量が上限を超えないか、developer.x.comの
  ダッシュボードで確認してください
- API利用料はご自身のクレジットカードに課金されます。想定外の頻度で実行されていないか、
  たまにGitHub ActionsのログとAPIの請求ダッシュボードを確認してください
- note・Instagramの下書きは、事実確認・表現チェックをしたうえで手動投稿してください(こちらは自動投稿しません)
- GitHub Actionsの無料枠は、プライベートリポジトリで月2,000分です。このワークフローの実行時間は
  1回数分程度なので、通常の使用では枠を超えることはまずありません
