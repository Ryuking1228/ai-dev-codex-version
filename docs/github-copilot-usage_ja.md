# GitHub CopilotでNexusを使う一番簡単な手順

GitHub Copilotでは、Claude Code pluginやCodex CLIをインストールしなくてもNexusの標準
workflowを利用できます。このリポジトリには次の4種類のCopilot設定があります。

| 種類 | 配置場所 | 役割 |
|---|---|---|
| Repository instructions | `.github/copilot-instructions.md` | 常に読み込むcommand対応表と安全ルール |
| Custom agents | `.github/agents/*.agent.md` | 新規アプリ、製品設計、アーキテクチャ、実装の専門モード |
| Prompt files | `.github/prompts/*.prompt.md` | 対応IDEで`/名前`から呼ぶ短い定型文 |
| Agent skills | `.github/skills/*/SKILL.md` | 依頼内容から自動発見するNexus workflowへの入口 |

詳しい処理は従来どおり`skills/**/SKILL.md`に一本化されています。Copilot用ファイルは
そこへ案内する薄いadapterなので、Claude Code・Codex・Copilotで手順が分裂しません。

## 最初の準備

```bash
git clone --recurse-submodules https://github.com/Ryuking1228/ai-dev-codex-version.git
cd ai-dev-codex-version
```

GitHub Copilotを有効にしたIDEなどで、このリポジトリを開きます。対応環境では
`.github/copilot-instructions.md`が自動で適用されます。

## ① 新しいアプリをゼロから作る

Copilotのagent選択から`nexus-app-builder`を選びます。VS Code、Visual Studio、JetBrains
IDEでは、chatに`/nexus-new-app`と入力する方法でも開始できます。その後ろへ次を追加します。

```text
保存先: /絶対パス/新しいアプリ名
アプリ名: アプリ名
目的: 何を解決するアプリか
利用者: 誰が使うか
主な流れ: 利用者が行う一番重要な操作
主な機能:
- 機能1
- 機能2
参考資料: /絶対パス/資料（なければ「なし」）

ローカル起動、画面確認、自動テストまで実行してください。
```

既にアプリがある保存先は上書きしません。デプロイとGitHubへのpushは別の作業なので、
必要な場合だけ明示して依頼します。

## ② 既存アプリを機能拡張・リファクタリングする

`nexus-architect` agentを選ぶか、chatで`/nexus-existing-app`を呼び、次を追加します。

```text
対象: /絶対パス/既存アプリ
変更内容: 追加したい機能、または直したい問題
完了条件:
- 条件1
- 条件2
出力言語: 日本語
```

最初に既存コードを調査して設計します。同じ依頼で実装まで必要なら「実装とテストまで」と
追記してください。既にNexusのbacklogが承認済みなら、`nexus-delivery` agentまたは
`/nexus-deliver-backlog`を使います。PRの承認とmerge前では、元のworkflowどおり停止します。

## ③ 機能を細かく決めず、製品案から整理する

`nexus-product` agentまたは`/nexus-product-design`を使います。製品の目的、対象利用者、
制約、参考資料だけを渡すと、仮説検証、scope、journey、機能、domain、品質要件の順に整理し、
その結果を`nexus-architect`へ引き継げます。

## モデルと料金について

Nexus本体の`haiku` / `sonnet` / `opus`は、作業の難しさを表す抽象tierです。Copilotでは、
現在のCopilot環境でユーザーが選んだmodelをcustom agentが引き継ぎます。

Codex用のLuna / Terra / Sol自動割り振りはCopilotでは実行しません。費用を抑える場合は、
定型作業にはCopilot側の低コストmodel、重要な設計・risk reviewには高性能modelを選びます。
利用可能なmodelと課金はCopilotのplan・利用環境によって異なります。

## うまく動かないとき

- 指示が適用されたか確認する: Copilotの回答にある参照一覧で
  `.github/copilot-instructions.md`を確認する
- `/nexus-new-app`が候補に出ない: prompt files対応のIDEか確認し、代わりに
  `nexus-app-builder` agentを選ぶ
- agentが表示されない: 通常のCopilot chatへ同じ依頼を書けばrepository instructionsと
  agent skillsから標準workflowを利用できる
- `codex exec`を実行しようとする: 停止して「CopilotではCodex model routerを使わない」と伝える

公式仕様はGitHubの[repository instructions](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions-in-your-ide/add-repository-instructions-in-your-ide)、
[custom agents](https://docs.github.com/en/copilot/reference/custom-agents-configuration)、
[agent skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills)を参照してください。
