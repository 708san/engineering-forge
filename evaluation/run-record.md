# 比較実験記録契約（v0.12-dev）
evaluation-v0.5.md と first-use.md に基づく記録手順。正式な比較を行う前に条件を固定し、実際の観測だけを残す。公開校正ケースは正式な未知案件の結果と混ぜない。
各試行には case_id, condition_id（比較条件）, repeat, model, environment, forge_revision（不使用ならnull）, input_revision, budget, outcome_observations, critical_violations, elapsed_seconds, human_questions, human_seconds, cost, rework, status, artifact_refs を記録する。未測定値はnullとし、0と混同しない。失敗・中断も保存する。入力と評価基準は別の管理主体で事前固定する。各必須成果の状態は met/unmet/unverified/not_due。metには観測根拠が必要で、設計で言及しただけでは達成ではない。評価者ごとの7軸と根拠、重大違反、必須成果の不足を別に記録する。
同一case_id/repeatで条件を対にして比較する。比較対象の欠測、環境差、評価者の非独立性を明記し、欠測を除外した都合のよい平均だけを出さない。重大違反と必須成果未達は品質点数で相殺しない。時間や費用の削減は製品品質との両面で評価する。正式比較の閾値・反復数は予備試行後に固定する。
この版で追加するのは試験用の公開入力と記録契約であり、比較結果ではない。別のAI・独立評価者を起動できる実行環境が必要。結果を捏造せず、実施できた条件のみ記録する。
