# __APP_NAME__

Codex用の新規アプリひな形です。React + FastAPI + PostgreSQLを接続した項目登録のサンプルを含みます。
実際のプロダクト要件は `docs/product.md` を書き換えてください。

## 起動と確認

前提: Python 3.10以上、Docker Engine/DesktopとCompose v2。ポート8000を空けてください。

```bash
python3 appctl.py up
# Dockerを動かしたPCで http://localhost:8000 を開く
# 項目を追加 → ページを再読込 → 保存を確認 → 削除
python3 appctl.py inspect --note '追加・再読込後の保持・削除・スマホ幅を確認'
python3 appctl.py verify
python3 appctl.py release-check
```

`inspect` は実際に確認した後だけ実行します。検証はフロントの型検査・ビルド、APIテスト、
隔離されたテストDBでの保存確認、Playwrightブラウザテストを含みます。
未実行や0件を合格にせず、コード変更後は前回の検証を無効にします。

`.env` は起動時にランダムなローカルDBパスワードで生成されます。Gitには含めません。
`down` は停止だけで、データ用ボリュームは削除しません。PostgreSQLのソフトウェアにライセンス費は不要ですが、
公開環境のサーバー・ストレージは利用先によって費用がかかります。

## 開発

Codexでこのディレクトリを開き、`AGENTS.md` に従って要件・画面・API・DB・テストを変更します。
Pythonのテストだけを素早く実行する場合:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt
PYTHONPATH=backend pytest backend/tests/test_api.py
```

フロントの高速開発は `cd frontend && npm ci && npm run dev`（Node 24）を使えます。
APIの接続先はlocalhost:8000です。ローカル確認後、必ず全体の `verify` を実行します。
DBの変更は `backend/migrations/` に新しい番号のSQLを追加します。適用済みSQLの書き換えは拒否します。

## デプロイ

Dockerfileは配布用イメージを作ります。公開先は未設定です。
このサンプルは認証を持たないため、公開前にプロダクトに必要なアクセス制御を実装してください。
`compose.yaml` はローカル用です。本番のTLS・秘密情報・DBバックアップ・マイグレーションの実行責任は
選んだ公開先で設定します。マイグレーションは `python -m app.migrate` で実行します。

公開先を決めたら `app-workflow.json` の `deploy.environment`、`deploy.command`（引数配列）、
`deploy.health_url`（HTTPSの `/api/health`）を設定します。秘密情報は環境変数・公開先のsecretへ設定します。
設定変更もソース変更なので、再度確認・検証した後に `python3 appctl.py deploy` を実行します。
成功の記録はデプロイコマンド完了と公開先のDBヘルスチェックの両方が通った場合だけ保存されます。

## 非公開GitHubへの保存

GitHub CLIを認証し、新規の **Private** リポジトリを作成してください。
公開リポジトリのforkではなく、独立した非公開リポジトリを使います。

```bash
git init -b main
git add .
git diff --cached --stat
git commit -m 'Initialize application'
gh repo create Ryuking1228/YOUR_APP --private
python3 appctl.py push --repo Ryuking1228/YOUR_APP
```

プッシュはコードの保存、デプロイはアプリの公開です。目的が別なので独立して実行できます。
`push` は宛先の非公開設定・所有者と作業ツリーを検査し、force-pushを使いません。
