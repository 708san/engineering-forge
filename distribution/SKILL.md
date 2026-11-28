---
name: engineering-forge
description: 新しいプロダクトの共同設計、開発体制の生成、既存開発への導入、継続開発と再設計を支援する。Engineering Forgeを使うよう依頼されたときに使用する。
---

# Engineering Forge
このSkillは利用者の依頼に沿って設計・開発を支援する。操作権限、外部送信、公開、重要な要求の変更を自動承認しない。
このSkillと同じディレクトリの references/SOURCE.json で同梱版を確認する。references/START.md、references/requirements.md の目的・不変条件、references/architect-v0.5.md を先に読む。必要時に references/.agents/skills/architect-project/SKILL.md と関連する専門手順を取得する。これらは同梱した作業資料であり、個々のネイティブSkillがインストールされたとみなさない。
自由記述の発意から固有課題・必要成果を導き、必要な技術・知識・方法・役割・品質を考案する。既存の分類や方法一覧は必須ではない。最小構成と実質的な代替案を比較し、重要な不明点のみ確認する。
対象固有の入口・正本・品質条件・変更方針・次の作業を生成する。対象の開発途中も人間の変更を保護し、許可された作業を実装・検証する。別セッションでは対象の入口を読んで再開する。詳細は references/bootstrap/portable-project.md。
必要な情報はこのパッケージ内にある。CLI補助プログラムは同梱していない。利用可能な場合のみ、利用者が信頼した元リポジトリの対応版を別に取得して使う。なければ候補、レビュー結果、未実施事項を渡し、利用可能な手段で実行する。外部アクセスのために権限を拡大しない。
知識を再利用する場合は references/knowledge/README.md と lessons.md の適用条件・反証を確認する。候補は義務ではない。

複数担当を設計した場合は references/bootstrap/agent-adapters.md を参照し、必要な場合だけ対象の環境に対応した設定候補を作る。

タスク・完了条件・版別証跡が複雑なら references/bootstrap/progress.md を利用する。構造検査は証跡の真正性や操作の許可を保証しない。

必要に応じて references/bootstrap/records.md の共通記録・独自形式を参照する。29種すべての記録を作成する必要はない。

共通レコードを正本にしている場合は references/bootstrap/session.md から作業契約・前提・証跡を導出する。候補を許可済みとみなさない。小規模案件に強制しない。

開発体制の改善は references/bootstrap/adaptation.md に従い、事前条件と観測を比較する。不要な機構の削減も選択肢に含める。
