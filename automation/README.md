# 本質のAI活用術 自動化スクリプト

GitHub Actions(クラウド)上で動くPythonスクリプトです。**PCの電源が入っていなくても実行されます。**
実行ログはGitHubの「Actions」タブでいつでも確認でき、失敗した場合もそこに残ります。

## 何をするか

| スクリプト | 内容 | 送信先 | 実行タイミング |
|---|---|---|---|
| `daily_sns.py` | Web検索でAI活用インフルエンサーの傾向を調べ、今日のX投稿案(単発+スレッド)を作成 | メール | 毎日 9:00 JST |
| `weekly_note.py` | 似た発信者をリサーチし、まだ扱っていない新テーマを自分で提案してnote新作(企画〜集客文まで)を作成。扱ったテーマは `themes_log.json` に記録し、二度と同じテーマを提案しない | メール | 毎週月曜 9:15 JST |
| `daily_instagram.py` | Instagram用画像(OpenAIで生成)+キャプションを作成、画像を添付 | メール(添付ファイルあり) | 毎日 8:00 JST |

いずれも**下書きを作ってメールで送るだけ**です。実際の投稿はご自身で行ってください。

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
3. **API keys** から新規キー(`sk-...`)を作成しコピーする(DALL-E 3 HDは1枚約$0.08)

### 3. Gmailアプリパスワードの発行(goliath24520@gmail.comで送信)

1. goliath24520@gmail.com で https://myaccount.google.com/security を開く
2. 「2段階認証」が無効な場合は先に有効化する(アプリパスワードには2段階認証が必須)
3. https://myaccount.google.com/apppasswords を開き、アプリ名(例:「note自動化」)を入力して作成
4. 表示された16桁のパスワード(スペースなしでOK)を控えておく

### 4. GitHubリポジトリを作る

1. https://github.com/new を開く
2. リポジトリ名を決める(例:`note-automation`)、**Private** を選択して「Create repository」
3. 作成後に表示されるリモートURLを控えておく(例:`https://github.com/あなたのID/note-automation.git`)

### 5. Secrets(暗号化された環境変数)を登録する

作成したリポジトリの **Settings → Secrets and variables → Actions → New repository secret** から、
以下5つをそれぞれ登録してください(値は前の手順で控えたもの):

| Secret名 | 値 |
|---|---|
| `ANTHROPIC_API_KEY` | `sk-ant-...` |
| `OPENAI_API_KEY` | `sk-...` |
| `GMAIL_ADDRESS` | `goliath24520@gmail.com` |
| `GMAIL_APP_PASSWORD` | (16桁のアプリパスワード) |
| `MAIL_TO` | `reon24520@gmail.com` |

### 6. このフォルダをGitHubにpushする

このプロジェクトフォルダ(`notehannbai2`)のルートで実行してください。

```bash
cd "C:\Users\reon2\OneDrive\デスクトップ\notehannbai2"
git init
git add .
git commit -m "note自動化の初期セットアップ"
git branch -M main
git remote add origin https://github.com/あなたのID/note-automation.git
git push -u origin main
```

`.env` ファイルは `.gitignore` で除外されるため、誤って公開される心配はありません
(APIキーはSecretsにのみ保存されます)。

### 7. 動作確認(手動実行)

GitHubのリポジトリページ → **Actions** タブ → 左側から実行したいワークフロー
(例:「Daily SNS Post」)を選び → 右側の「Run workflow」ボタンを押すと、その場ですぐ実行できます。
数十秒〜数分後にメールが届けば成功です。失敗した場合はActionsタブの実行ログに詳細が表示されます。

以降は、設定した時刻に自動で実行されます(PCの電源状態に関係なく動きます)。

---

## テーマの拡張について

`weekly_note.py` は固定リストではなく、毎回Web検索で他のAI活用系インフルエンサーの発信傾向を調べ、
`themes_log.json` に記録済みの過去テーマと重複しない新テーマを自分で提案してから執筆します。
そのため運用を続けるほどテーマの引き出しが自然に広がっていきます。
`themes_log.json` はワークフロー実行のたびに自動更新・コミットされるので、手動で編集する必要はありません。

---

## (オプション)ローカルPCでも動かしたい場合

`run_daily_sns.bat` / `run_daily_instagram.bat` / `run_weekly_note.bat` を使えば、
このPC上でも従来通りタスクスケジューラ経由で実行できます。ただしPCの電源が入っている必要があるため、
基本的にはGitHub Actions側の実行のみで十分です。ローカル実行する場合は `.env` ファイルを
`.env.example` を元に作成してください。

---

## 既知の制約・注意点

- API利用料はご自身のクレジットカードに課金されます。想定外の頻度で実行されていないか、
  たまにGitHub ActionsのログとAPIの請求ダッシュボードを確認してください
- 生成内容は事実確認・表現チェックをしたうえで手動投稿してください(自動投稿はしません)
- GitHub Actionsの無料枠は、プライベートリポジトリで月2,000分です。このワークフローの実行時間は
  1回数分程度なので、通常の使用では枠を超えることはまずありません
