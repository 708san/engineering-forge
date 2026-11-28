# 開発体制を試行・評価して改善する（v0.15-dev）
AIが方法・役割・協調・ツールを自由に改善する。失敗原因を製品、知識、方法、組織、環境、権限等から分析し、既存手法の簡素化や変更しない選択も含める。改善は機構の数や新規性ではなく成果で判断する。
## 小さな試行
1. 観測した問題と根拠、改善仮説、比較可能な範囲、停止条件、復元方法を先に決める。重要な保護条件と実際の操作権限は別に維持する。
2. 比較用の指標・単位・測定手順・改善方向・許容低下・最小改善を事前に定義し、計画を候補作成者から独立して保存する。定性的評価は別途根拠付きレビュー。品質や安全の重大な低下を効率改善で相殺しない。
3. 変更を別領域で試行し、同等の条件で旧版と新版を測定する。環境・予算の違い、失敗、欠測を記録する。確認待ちがあっても無関係な作業を続ける。
4. 事前条件との比較、保護条件の比較、意味レビューを行う。採用・限定試行・再設計・棄却の判断と根拠を残す。候補の自動採用・共有はしない。
## 任意の数値比較補助
`python3 -B forge.py trial PLAN.json` は計画JSONの内容指紋を出す。信頼できる別領域で保存する。
planの項目: project_id, hypothesis, scope, baseline_revision, candidate_revision, rollback, stop_conditions（文字列）、metrics（配列）。metricは id, unit, procedure, direction（higher/lower）, max_regression（非負の数値）, min_improvement（非負の数値）, required（真偽値）。
observationsの項目: project_id, plan_sha256, baseline_revision, candidate_revision, stop_observations（発生した停止理由の配列）, measurements（配列）。各測定は id, baseline, candidate, baseline_ref, candidate_ref。数値・参照の未測定はnull。参照は実測ログ等の識別子であり、存在や真正性を自動認証しない。
`python3 -B forge.py trial PLAN.json OBS.json --expect RETAINED_SHA256`
共通レコード使用時は `--records OLD_DIR OLD_MANIFEST NEW_DIR NEW_MANIFEST` を任意追加し、保護・履歴・基準比較も行う。比較先の版と試行の版が一致することは別途レビューする。
終了0は比較上レビュー候補（採用ではない）または指紋出力、2は改善未確認/要レビュー/停止、1は検査不能。必須測定の欠測は改善認定しない。許容を超えた低下や停止理由は他の改善で相殺しない。数値比較の意味、計画の事前確定、測定条件・真正性・保護要求の全体適合は検査しない。少数試行から一般的な優越性を主張しない。
