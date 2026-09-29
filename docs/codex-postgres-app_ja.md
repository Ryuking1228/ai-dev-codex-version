# Codex + PostgreSQLで新規アプリを作る

この拡張はWataru Fukatsu氏の上流プロジェクトを土台に、個人の新規アプリ開発向けの実行経路を追加します。
既存のproduct・architect・scalardb・infraの動作とライセンスを保持しています。

## 想定する流れ

1. 作りたいプロダクトの用途・利用者・受入基準をCodexに伝える。
2. UI・バックエンド・PostgreSQLを実装する。
3. 自分のPCのlocalhostで一連の操作とDB保存を確認する。
4. 自動テストを実行し、問題があれば修正する。
5. 公開先を設定してデプロイし、公開先の動作を確認する。
6. コードを自分の非公開GitHubリポジトリに保存する。

テストは開発中も小さく実行します。手順4はローカル確認後の総合確認です。
GitHubへのプッシュは開発途中にも可能で、デプロイとは独立しています。

## 使い方

Codexでこのリポジトリを開き、例えば次のように依頼します。

> /app:start 営業案件を管理するアプリを作りたい。自分だけで使う。
> 案件名・顧客名・金額・進捗を登録し、一覧と更新ができる。
> PostgreSQLを使い、localhostで確認してテストする。保存先は自分の非公開GitHub。

基盤だけ生成する場合:

```bash
python3 tools/new-app.py ../my-app --name my-app
cd ../my-app
python3 appctl.py up
```

Dockerを動かしているPCで `http://localhost:8000` を開きます。クラウド実行環境のlocalhostは
利用者のPCのlocalhostとは別です。Python 3.10以上とDocker Compose v2が必要です。
アプリのフォルダーをCodexで開き、そちらのAGENTS.mdに沿って改修します。

## 技術構成

| 対象 | 構成 |
|---|---|
| UI | React + TypeScript + Vite |
| API | Python + FastAPI、通常のPostgreSQL接続 |
| DB | PostgreSQL、SQLマイグレーション、永続ボリューム |
| ローカル起動 | Docker Compose、127.0.0.1:8000のみ公開 |
| API検証 | pytest、入力検証、API契約、Fakeによる単体テスト |
| DB検証 | 専用の一時PostgreSQL、接続を開き直して保存確認 |
| UI検証 | Playwright、追加→再読込→削除、モバイル幅 |
| 配布 | マルチステージDockerfile、指定先へのデプロイコマンド |
| 保存 | PRIVATE確認、所有者確認、force-push禁止 |

PostgreSQL自体は無償利用できるソフトウェアです。ホスティングの無料枠や継続無償を保証しません。
Docker Composeによるlocalと、公開先未定のdeployment hookは既存infraナレッジバンドルの対象外です。
この追加経路はTerraform/Kubernetesやマルチクラウドを前提にしません。

## 完了条件

`appctl.py verify` は実行結果を `.app-state/verification.json` に保存します。
テスト0件・未実行・失敗・skipを合格にしません。コードの指紋が変わったら検証済み状態を失効させます。
UI確認は実際に操作してから `inspect --note` で記録します。自動検証の代替にはなりません。
再確認後に `release-check` が通るとデプロイ手順へ進めます。

ひな形の検証は出発点であり、AI Dev Loopの全8段階品質ゲートを通過したという意味ではありません。
SAST・依存関係監査・認可検査・業務受入条件はプロダクトの要件に応じて追加します。

## デプロイの範囲

現時点で公開先やクラウドアカウントは指定されていません。デプロイ実行は未設定です。
公開先を決めてから `app-workflow.json` に環境名・引数配列のコマンド・HTTPSヘルスURLを設定します。
秘密情報はGit管理ファイルに記入しません。設定変更後は再検証が必要です。
公開前にアクセス制御、TLS、DB接続、マイグレーション、バックアップと復元を公開先に合わせます。
元のItemsサンプルにエンドユーザー認証はありません。

## 由来

上流作者: https://github.com/wfukatsu
元の著作権表示はルートのLICENSEに保持しています。生成アプリにもLICENSEをコピーします。
追加機能は `skills/app/start/`、`tools/new-app.py`、`templates/codex-postgres-app/` にまとまっています。
