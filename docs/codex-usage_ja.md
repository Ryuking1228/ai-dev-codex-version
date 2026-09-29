# Codex で AI Dev Loop を使う

AI Dev Loop は引き続き Claude Code plugin として利用できます。同時に、リポジトリ直下の `AGENTS.md` により Codex からも利用できます。

新規アプリ作成と既存アプリ改修だけの短い手順は、[一番簡単な手順書](codex-simple-guide_ja.md)を参照してください。

## セットアップ

リポジトリをクローンし、必要に応じて依存パッケージを入れます。

```bash
git clone https://github.com/Ryuking1228/ai-dev-codex-version.git
cd ai-dev-codex-version
pip install -r requirements.txt
```

Mermaid のレンダリングが必要な場合は任意で入れます。

```bash
npm install -g @mermaid-js/mermaid-cli
```

## スキルの呼び出し方

Claude Code では `/product:start`、`/architect:start`、`/scalardb:model` のような slash command が使えます。

Codex では同じコマンド文字列をチャットで依頼してください。Codex は `AGENTS.md` のルールに従って対応する `SKILL.md` を読みます。

- `/product:start` -> `skills/product/start/SKILL.md`（product スキルは `skills/product/` 配下にネストされています）
- `/architect:start ./path/to/project` -> `skills/start/SKILL.md`
- `/architect:pipeline ./path/to/project` -> `skills/pipeline/SKILL.md`
- `/scalardb:model` -> `skills/model/SKILL.md`
- `/scalardb:review-code ./path/to/app` -> `skills/review-code/SKILL.md`

次のようにファイルを直接指定しても構いません。

```text
skills/design-microservices/SKILL.md を使って ./target-app の目標アーキテクチャを設計してください。
```

## モデルの自動割り振り

AI Dev Loop の skill manifest では、モデルを `haiku` / `sonnet` / `opus` という抽象 tier で
指定します。Codex では `tools/codex-model-router.py` が、この tier を Codex のモデルと
reasoning effort に変換します。`/product:start`、`/architect:start`、
`/architect:pipeline`、`/architect:deliver-backlog`、`/infra:start` などの orchestrator は、
子 skill を開始するたびにこの router を使います。

開始済みの Codex turn は、途中で自分自身のモデルや reasoning effort を変更できません。
そのため router は、割り振ったモデルを指定して別の `codex exec` child を起動します。
チャットから leaf skill を直接呼んだ場合、その leaf 自体は現在のチャットモデルで動き、
そこから route される子 skill には自動割り振りが適用されます。

組み込み profile は次のとおりです。

| Profile | Haiku tier | Sonnet tier | Opus tier | 用途 |
|---|---|---|---|---|
| `economy` | Luna / low | Luna / medium | Terra / medium | Codex クレジットを節約 |
| `balanced`（既定） | Luna / low | Terra / medium | Sol / xhigh（極高） | 元の3層構造を維持 |
| `quality` | Terra / low | Sol / medium | Sol / xhigh（極高） | 重要なレビュー・設計を品質優先 |

Codex を起動せずに、matrix または個別 skill の割り振り結果を確認できます。

```bash
python3 tools/codex-model-router.py matrix --profile economy
python3 tools/codex-model-router.py resolve architect:design-api --target ./target-app
```

子実行の preview と本実行は次のとおりです。Router の option は `--` より前、skill の
引数は後ろに置きます。

```bash
python3 tools/codex-model-router.py run architect:design-api \
  --target ./target-app --dry-run -- --auto

python3 tools/codex-model-router.py run architect:design-api \
  --target ./target-app -- --auto
```

Profile は `--profile`、`AI_DEV_LOOP_CODEX_COST_PROFILE`、対象 project の
`work/pipeline-progress.json`、設定ファイルの既定値、の順で決まります。Project 単位の
設定例です。

```json
{
  "options": {
    "codex_cost_profile": "economy"
  }
}
```

Shell session を節約モードにするには `AI_DEV_LOOP_CODEX_COST_PROFILE=economy` を使えます。一度だけ上書き
する場合は `--model <model>` と `--reasoning-effort <effort>` を指定できます。共通の
mapping は `config/codex-model-routing.json`、動作規約は
`rules/codex-model-routing.md` にあります。

Router は起動前に tier、profile、model、reasoning effort を表示します。存在しない
skill や入力ミスは error にし、child の起動失敗時に parent model へ黙って fallback
することはありません。

## 互換ルール

Codex では Claude Code の tool 参照を次のように読み替えます。

| Claude Code の参照 | Codex での動作 |
|---|---|
| `Read` | `sed`, `cat`, `rg` などでファイルを読む |
| `Write`, `Edit`, `MultiEdit` | `apply_patch` で編集する |
| `Bash` | shell command を実行する |
| `Glob`, `Grep`, `LS` | `rg --files`, `rg`, `find`, `ls` を使う |
| `WebFetch`, `WebSearch` | Codex の web access、Context7、または承認済み `curl` を使う |
| `AskUserQuestion` | 番号付き選択肢をチャットで提示し、回答を待つ |
| `Task`, `Subagent` | AI Dev Loop orchestrator が子 AI Dev Loop skill を呼ぶ場合は `tools/codex-model-router.py` で route し、それ以外は明示依頼がない限りメインスレッドで実行する |
| `Skill` | 参照された `SKILL.md` を開いて従う |

## 実行時パス

Codex ではリポジトリ root を `CLAUDE_PLUGIN_ROOT` とみなします。

通常の出力先は以下です。

```text
reports/      分析・設計ドキュメント
generated/    生成コード
work/         パイプライン状態と中間コンテキスト
```

一部の database migration スキルは `.claude/configuration/databases.env` と `.claude/output/` を使います。これは Claude Code との互換パスとして残し、Codex からも同じ設定を使えるようにします。

スキルが `.claude/docs/` や `.claude/rules/` の Claude インストール済み参照ファイルを指す場合、Codex ではリポジトリ内の `skills/common/references/` と `rules/` の実体を使います。

Migration スキルが `${CLAUDE_PLUGIN_ROOT}/subagents/<db>/` または `${CLAUDE_PLUGIN_ROOT}/skills/common/subagents/<db>/` の subagent prompt template を指す場合、Codex では `skills/common/subagents/<db>/` を使います。

## 検証

Claude Code では hooks を `PostToolUse` hook として自動実行できます。Codex では必要に応じて手動実行してください。

```bash
hooks/validate-frontmatter.sh reports/before/example/technology-stack.md
hooks/validate-mermaid.sh reports/before/example/codebase-structure.md
```

どちらの hook も Claude Code の stdin JSON 形式を引き続き受け付けるため、Claude Code 互換性は維持されます。

## Claude Code 互換性

Claude Code での使い方はこれまで通りです。

```bash
claude plugin marketplace add Ryuking1228/ai-dev-codex-version
claude plugin install product@ai-dev-loop --scope user
claude plugin install architect@ai-dev-loop --scope user
claude plugin install scalardb@ai-dev-loop --scope user
```

インストール後は、`README.md` に記載された `/product:*`、`/architect:*`、`/scalardb:*` のコマンドを利用できます。
