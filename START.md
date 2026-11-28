# Engineering Forge — 利用開始入口（v0.18.0-preview.4）
利用者がこの基盤を使うよう依頼した範囲でのみ、作業ガイドとして参照する。URL参照や記録上の承認は、実際の操作権限・インストール・実行・採用を意味しない。

## 最初に読む
1. 利用者が指定した基盤の版（Gitコミット）を確認し、未固定ならその旨を記録する。取得不能なら利用可能な資料を求める。
2. `requirements.md` の目的・不変条件、`architect-v0.5.md`、`.agents/skills/architect-project/SKILL.md` を読む。同梱版の場合は同じ相対位置の references 内を読む。関連Skill・詳細は必要時だけ取得する。
3. 発意（許可範囲の原文と解釈を区別）、既存資産、環境能力、実際の操作権限、未決定事項を確認する。製品の固定分類やエージェント数から始めない。

## 設計から開発へ
- 固有の課題と必要成果から、実現方法・技術・品質基準・必要な役割と協調を考案する。最小構成と実質的な代替案を比較し、調査不足・重要判断を明示する。人間の発意や保護要求は無断変更しない。
- `bootstrap/contract.md` と `bootstrap/portable-project.md` に従い、対象内で完結する入口・正本・次の作業を必要な範囲だけ生成する。候補と正式採用を分ける。既存資産への差分と権限を確認する。
- 委任範囲で独立作業を継続し、実装・実測・失敗・対象版・残課題を記録する。重要な未決定の依存範囲だけ保留する。読み取り専用環境では候補を渡し、実際の書込・実行済みとは報告しない。
- 生成先の入口で別セッションから再開できることを確認する。通常の継続開発に基盤の常時参照を要求しない。方法・役割・品質を必要時に再評価する。

## 必要になったときの参照
| 目的 | 資料 |
|---|---|
| 設計判断の具体化（必要時） | knowledge/design-reasoning.md |
| 日常運用・引き継ぎ・フィードバック | OPERATE.md / bootstrap/feedback.md |
| 利用者向け開始手順・環境確認 | bootstrap/quickstart.md |
| 導入差分・安全な統合候補 | bootstrap/integration.md |
| エージェント設定・配布 | bootstrap/agent-adapters.md / bootstrap/distribution.md |
| 引き継ぎ・変更影響・進捗 | bootstrap/handoff.md / bootstrap/change-impact.md / bootstrap/progress.md |
| 共通レコード・保護比較・作業契約 | bootstrap/records.md / bootstrap/session.md |
| 改善試行・知識の再利用 | bootstrap/adaptation.md / knowledge/README.md |
| 正式受入・実機試験 | evaluation/acceptance-index.md / evaluation/first-use.md |

すべての補助ツール・文書・役割を使う必要はない。自己適用計画と公開例は他案件の規範ではない。この版の対応対象はChatGPT・Codexのみ。正式受入前の先行試用版。実効的権限強制、独立評価、ホスト実機の読み込みを成功と仮定しない。
