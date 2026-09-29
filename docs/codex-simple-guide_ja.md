# CodexでAI Dev Loopを使う一番簡単な手順

GitHub Copilotを使う場合は、[GitHub Copilot版の簡単な手順](github-copilot-usage_ja.md)を
参照してください。

覚えることは2つだけです。

- 新しいアプリを作る: `/app:start`
- 既存アプリを改修する: `/architect:start` → `/architect:deliver-backlog --export`

モデルは自動で選ばれます。`codex-model-router.py`を自分で実行する必要はありません。

## 最初にすること（共通）

まだcloneしていない場合は、次のコマンドを実行します。

```bash
git clone --recurse-submodules https://github.com/Ryuking1228/ai-dev-codex-version.git
cd ai-dev-codex-version
```

Codexで、cloneした`ai-dev-codex-version`フォルダーを開きます。例えば次のような
絶対パスになります。

```text
/Users/あなたのユーザー名/Downloads/ai_dev_loop/ai-dev-codex-version
```

作成先・改修対象は、必ず絶対パスで指定してください。

## ① 新しいアプリをゼロから作りたい

Codexのチャットへ、次の文章をコピーして必要な部分だけ書き換えます。

```text
/app:start

新しいアプリをゼロから作ってください。
保存先: /絶対パス/新しいアプリ名
アプリ名: アプリ名
目的: 何を解決するアプリか
利用者: 誰が使うか
主な機能:
- 機能1
- 機能2
- 機能3
参考資料: /絶対パス/資料（なければ「なし」）

ローカル起動、画面確認、自動テストまで実行してください。
```

トラック配車アプリの例です。

```text
/app:start

新しいトラック配車アプリをゼロから作ってください。
保存先: /Users/ohshiroryuki/Downloads/life/projects/track-delivery-app
アプリ名: track-delivery-app
目的: 配送依頼へトラックとドライバーを割り当て、配車状況を管理する
利用者: 配車担当者
主な機能:
- 配送依頼の登録と一覧表示
- トラック・ドライバーの割り当て
- 配送状況の更新
参考資料: /Users/ohshiroryuki/Downloads/life/projects/track-delivery-apps/docs/

ローカル起動、画面確認、自動テストまで実行してください。
```

あとはCodexから質問されたときだけ回答します。次の3点が報告されたら完了です。

1. アプリが保存先に作成された
2. ローカル画面を確認できた
3. `python3 appctl.py verify`が成功した

既にコードがあるフォルダーへは`/app:start`で上書きしません。その場合は次の「既存アプリ」の手順を使います。

## ② 既存アプリを機能拡張・リファクタリングしたい

### 1. 変更内容を調査・設計する

Codexのチャットへ次の文章をコピーします。

```text
/architect:start /絶対パス/既存アプリ

この既存アプリを調査して、次の変更を設計してください。
変更内容: 追加したい機能、または直したい問題
完了条件:
- 条件1
- 条件2
出力は日本語にしてください。
```

例:

```text
/architect:start /Users/example/projects/existing-app

この既存アプリを調査して、配送依頼の一括割り当て機能を設計してください。
完了条件:
- 未割り当ての配送依頼を複数選択できる
- 空いているトラックとドライバーを割り当てられる
- 既存の個別割り当て機能を壊さない
出力は日本語にしてください。
```

Codexから質問されたら回答し、設計完了の報告を待ちます。

### 2. 設計した変更を実装する

対象アプリがGitHubまたはGitLabのリポジトリなら、同じチャットで続けて次だけ入力します。

```text
/architect:deliver-backlog --export --lang=ja
```

Codexが作業項目を作り、実装、テスト、レビュー、PR/MR作成まで進めます。PR/MRの承認とマージ前には止まるので、内容を確認して回答してください。

この手順には、対象リポジトリに対する`gh`または`glab`のログインが必要です。GitHub/GitLabを使わずローカルだけで変更する場合は、設計完了後に次のように依頼します。

```text
先ほど作成した設計レポートに従って、対象アプリの実コードを変更してください。
必要なテストを追加して実行し、変更ファイルとテスト結果を報告してください。
PR作成とマージは不要です。
```

## 困ったとき

- 新規作成先に既にコードがある: ②の手順を使う
- Codexが対象を見つけられない: 相対パスではなく絶対パスにする
- コストを下げたい: 最初の依頼に「モデルプロファイルは`economy`を使って」と追加する
- モデルを確認したい: `python3 tools/codex-model-router.py matrix`を実行する
