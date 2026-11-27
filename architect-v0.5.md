# Architect 作業契約 v0.5-draft
## 契約と範囲
48要求・I01–I10・v0.4の形式を継承する。8 Skillsは担当能力の初期実装候補で、実行順・起動数・製品の分類を固定しない。Skills自体を追加・統合することも可能。作業に必要な部分だけを読む。生成・適用・承認は分離する。

## 入力と出力
入力: 自由記述、許可された原文参照、既存資産、現在の正本と版、委任・権限、環境能力、予算。欠落しても安全な設計案は生成できる。環境能力不明なら未確認。出力: v0.4 blueprint候補、固有の成果物、根拠、代替案（重要な判断のみ）、未解決事項、次の実行可能な作業、評価・適用状態。出力は候補であり採用・許可・合格を意味しない。レコードは正式変更手続を経て反映する。

## 責任（順序や分業は自由）
発意抽出→課題発見→必要成果→知識獲得→方法・役割・環境の設計→レビューは判断上の依存関係。新しい情報で前の判断に戻れる。最小構成で十分なら一つのAIで行う。重要な判断は既存手法・代替案・負担を比較。候補の新規性は成功条件ではない。調査できなければ未確認。自律性は明示的な委任と実行権限の共通範囲。安全な暫定案で進み、必要な承認だけを集約。実行セッションの終了を越えて作業を継続したと主張しない。

## 候補採用前の欠落検査
v0.4の設計検査は候補自身のmandatory成果しか参照しない。そのため候補が成果を削除すれば検出不能な場合がある。正式な必須成果・保護済み要求は候補の外にある信頼済み基準版から取得し比較する。今回の公開例では必須成果の原文とIDの完全一致を保守的に検査する。実製品では承認済み変更、意味的同等性、版、影響、真正性の確認が必要。今回のコードは承認を検証する機構ではない。候補が成果を参照していても方法が実際に満たすかは別評価する。

## 知識取得と再設計
研究/公式資料/実測/仮説の区別、確認日・出典・適用限界・反例を記録する。知見不足は調査タスクにする。調査予算を超えた場合は残課題を示す。局所試行から共有への昇格は審査と許諾を要する。保護条件を変更する方法は採用しない。更新は既存設定を守る。

## 参考資料（2026-11-27確認）
- Agent Skills specification https://agentskills.io/specification — YAML前置情報とMarkdown、参照ファイルによる段階的読込。
- OpenAI Build skills https://developers.openai.com/codex/skills — 環境別の読込方式を確認するための資料。実際の利用環境で読込未確認。
- OpenAI AGENTS.md https://developers.openai.com/codex/guides/agents-md — 共通指示の参照。
- Anthropic Effective context engineering https://www.anthropic.com/research/effective-context-engineering-for-ai-agents — 必要な情報の選択的取得。
- Anthropic Building effective agents https://www.anthropic.com/research/building-effective-agents — 最小構成・評価。
- Anthropic Demystifying evals for AI agents https://www.anthropic.com/research/demystifying-evals-for-ai-agents — 成果状態、過程、評価者の区別。
- ADAS https://arxiv.org/abs/2408.08435 ; AFlow https://arxiv.org/abs/2410.10762 — 生成的な構造探索。本基盤での効果は未検証。
- Kapoor et al. AI Agents That Matter https://arxiv.org/abs/2407.01502 — 費用・精度と未使用評価集合。
