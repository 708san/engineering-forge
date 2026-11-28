# 要求・実装対応監査（v0.12-dev）
2026-11-28。対象設計: requirements.md、対象実装: 4d004c1de4830460ea8c4c0bd70259b4a8d08f4a。これは自己レビューの対応付けであり、仕様承認・独立監査・受入合格表ではない。
「部分実装」は一部の補助機能があることのみ、「設計手順」はAI向けの手順があることのみ、「未移行・未実装」は現在のGitHub上に実行可能な全体機構がないことを表す。旧v0.6は会話内のアーカイブを指す。正式受入試験A/B/Cは全体として未実施。個々の単体試験の成功をそれらの合格に置換しない。
集計: 設計手順 23件 / 部分実装 22件 / 未移行・未実装 2件 / 将来候補 1件。全48件を対応付けた。旧版との逐条完全性は別の未完作業。

| ID | 優先 | 到達点 | 現行資料・機能（Skill名は .agents/skills/ 配下） | 受入ID | 未達・次の検証 |
|---|---|---|---|---|---|
| R01 | M | 設計手順 | START.md; discover-intent | A01,A02 | 既存リポジトリと望ましい状態の独立実機試験 |
| R02 | M | 設計手順 | discover-intent; requirements.md §2 | A01,A03 | 原文と来歴の版管理・訂正・非保存の検証 |
| R03 | M | 設計手順 | discover-intent; review-blueprint | A01,A04 | 曖昧な要求・矛盾の発見能力の実証 |
| R04 | M | 設計手順 | discover-intent; design-operations | A04,A05 | 固有リスク・不確実性の独立評価 |
| R05 | M | 設計手順 | architect-project; generative-architecture.md | A05,A06 | 固有観点の発見、省略・追加の妥当性 |
| R06 | M | 設計手順 | design-method | A05,A06 | 手法間競合の評価と旧要求文言の改訂判断 |
| R07 | M | 設計手順 | design-operations | A06,A07 | 技術選択の根拠・代替案を実案件で評価 |
| R08 | M | 部分実装 | design-operations; forge_integrate.py | A07,A08 | 対象ごとのGitHub権限・運用設計と実機確認 |
| R09 | M | 設計手順 | design-operations | A07,A09 | 実配布・互換性・移行・廃止の検証 |
| R10 | M | 設計手順 | design-method; review-blueprint | A04,A06 | 人間の負担と技術的負債の測定 |
| R11 | M | 部分実装 | design-organization; forge_agents.py | A06,A10 | 新規役割・協調の意味評価と実起動 |
| R12 | M | 部分実装 | design-organization; bootstrap/agent-adapters.md | A10,A11 | 完全な個別作業契約の生成・検証 |
| R13 | M | 部分実装 | forge_handoff.py; bootstrap/handoff.md | A03,A12 | 別セッションで必要文脈の取得を実証 |
| R14 | M | 部分実装 | design-organization; forge_integrate.py | A13 | 複数実行主体の領域分離・統合・並行試験 |
| R15 | M | 部分実装 | forge_integrate.py; forge_impact.py | A03,A14 | 実案件で人間の変更を受けた意味的影響の評価 |
| R16 | M | 設計手順 | requirements.md §6; design-organization; doctor | A08,A11,A15 | 承認と実行権限の真正性・強制 |
| R17 | M | 設計手順 | discover-intent; adapt-harness; forge_progress.py | A11,A15 | 判断期限・代替案・保留範囲の正式管理 |
| R18 | M | 部分実装 | forge_progress.py; bootstrap/progress.md | A11,A12,A16 | 状態遷移・実作業の永続化・再開の実証 |
| R19 | M | 部分実装 | forge_impact.py; forge_validate.py; forge_progress.py | A04,A17 | 共通レコードの型付き追跡と全体検証 |
| R20 | M | 部分実装 | adapt-harness; forge_integrate.py | A14,A15,A17 | 正式仕様と提案の承認・履歴・変更契約 |
| R21 | M | 未移行・未実装 | requirements.md §5; 旧v0.6 schemas | A17,A18 | 元スキーマの完全移行と汎用参照検証 |
| R22 | M | 部分実装 | forge_validate.py; forge_progress.py; forge_impact.py | A15,A16,A17,A19 | 共通レコード・保護変更・依存循環の完全検査 |
| R23 | M | 設計手順 | design-method; review-blueprint | A05,A09,A19 | 固有の品質特性・妥当性評価の実証 |
| R24 | M | 部分実装 | forge_progress.py; forge_handoff.py; audit/ | A09,A17,A19 | 証跡の真正性・部分変更時の有効性評価 |
| R25 | M | 設計手順 | review-blueprint; evaluation/first-use.md | A09,A10,A19 | 独立主体による受入・リリース判定 |
| R26 | M | 部分実装 | design-operations; forge_integrate.py | A08,A20 | 信頼境界の実環境試験・秘密漏えい防止 |
| R27 | M | 設計手順 | design-operations; knowledge/README.md | A05,A20 | 具体案件でライセンス等の適用判断を評価 |
| R28 | M | 部分実装 | forge.py doctor; bootstrap/quickstart.md | A08,A21 | ChatGPT/Codexネイティブ機能・実権限の確認 |
| R29 | M | 部分実装 | forge_agents.py; forge_pack.py | A12,A21 | ネイティブ設定読込・別環境の引き継ぎ |
| R30 | M | 部分実装 | forge_preview.py; forge_integrate.py | A13,A18,A22 | 採用後の復元・取り外し・競合下の安全性 |
| R31 | M | 設計手順 | review-blueprint; audit/ | A05,A06,A21 | 別主体による設計品質と過剰工程の評価 |
| R32 | M | 部分実装 | adapt-harness; knowledge/lessons.md | A23 | 知識に基づく実際の方法改善と効果確認 |
| R33 | S | 設計手順 | knowledge/README.md | A23 | 共有許可の確認と別案件での再利用実証 |
| R34 | M | 設計手順 | research-knowledge; knowledge/README.md | A23 | 外部知識の探索・出典・適用の実案件評価 |
| R35 | M | 設計手順 | evaluation-v0.5.md; evaluation/run-record.md | A24 | 事前登録・独立評価者・複数条件の比較実験 |
| R36 | M | 設計手順 | START.md; bootstrap/quickstart.md | A01,A12 | 新規ChatGPT・Codexから自然言語だけで利用 |
| R37 | M | 部分実装 | forge_pack.py; examples/uncertain-order | A18,A22 | 多様な生成先の独立保守、非Git環境での利用 |
| R38 | M | 部分実装 | forge_pack.py; forge_handoff.py | A18,A22 | 全レコード・移行・依存版の完全管理 |
| R39 | M | 部分実装 | bootstrap/quickstart.md; requirements.md | A06,A21 | 任意補助機能から実行境界の強制への移行 |
| R40 | F | 将来候補 | requirements.md §3 | A18 | 新規アダプター追加時の拡張性を確認 |
| R41 | M | 設計手順 | architect-project; discover-intent | C01,C02,C03 | 未見・複合案件で固有現象を発見できるか |
| R42 | M | 設計手順 | research-knowledge; design-method | C02,C04,C05 | 新規知識の取得・局所試行・失敗からの学習 |
| R43 | M | 部分実装 | forge_validate.py; forge_agents.py | C01,C02,C06 | 未知成果物・役割・評価法の実案件検証 |
| R44 | M | 未移行・未実装 | 旧v0.6 schemas/project.schema.json; schemas/record.schema.json | C06,C07,C08 | 任意拡張スキーマの安全な登録・検証・未知保存 |
| R45 | M | 部分実装 | forge_validate.py; design-method | C04,C08,C09 | 信頼済み基準の真正性・意味的保護条件・権限 |
| R46 | M | 設計手順 | evaluation-v0.5.md; evaluation/calibration-v0.12.md | C01,C03,C05,C10 | 未見案件の事前登録期待成果による独立比較 |
| R47 | M | 設計手順 | knowledge/README.md; adapt-harness | C04,C11 | 共有許可・独立採否と局所変更の分離を実証 |
| R48 | M | 部分実装 | forge.py; bootstrap/quickstart.md | C12 | AI利用不可時の手動運用を別環境で確認 |

## 完成判定に向けた重点
1. 既存の検査器・配布・導入の独立監査と、不整合の再現・修正。旧設計資産の完全移行とR19/R21/R44の汎用レコード検証を優先する。旧スキーマを新しい別形式で無断置換しない。
2. 重大条件（保護要求、権限、証跡、個人情報、既存編集）について実際の信頼境界と運用を確認する。
3. 別のChatGPTとCodexを使う公開校正および未見案件の正式比較。プロジェクト固有の成果・人間の負担・実装品質を測り、エージェント数や文書数を成功指標にしない。
4. 受入判定の根拠と未検証事項を保存し、別主体のレビュー後にmainへ統合する。現段階は実験的利用候補であり正式リリースではない。
