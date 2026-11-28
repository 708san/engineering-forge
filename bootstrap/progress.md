# 開発の進捗・証跡の任意検査（v0.12-dev）
目的は、未完了の前提に依存する作業を誤って開始・完了扱いせず、無関係な作業は継続できるようにすること。既存の課題管理を置換する必要はない。AIが個別の方法・タスク・責任・完了条件を考案する。小規模案件なら文章による管理でもよい。

## 入力と運用
ledger.json は project, tasks, evidence の三項目。各 task は id, purpose, state, parent（親IDまたはnull）, depends_on（実行の前提となるIDの配列）, checks（空でない完了条件の識別子の配列）, owner（担当名、自由記述）。状態は requirements.md §6 に従う。親子は整理上の関係であり、実行順序を強制しない。親の完了が子に依存する場合は depends_on に明示する。完了条件は試験・人間評価・レビューなどプロダクト固有のものを使用する。
各 evidence は task_id, check, revision, verdict（pass/fail/blocked/not_run）, environment, procedure, reference（ログ等への参照）。全項目は記録された観測で、承認・実行の証明ではない。同じtask/check/revisionの重複は拒否する。試行が複数なら元ログを残した上で、どの結果を採用するか別途レビューして一件に集約する。

    python3 -B forge.py progress LEDGER.json --target TRUSTED_GIT_WORKTREE
    python3 -B forge.py progress LEDGER.json --revision EXTERNALLY_SUPPLIED_REVISION

--target は信頼できる静止したクリーンなGit作業領域のHEADを実際に取得する。--revision は手動で与えた対象版であり真正性は確認しない。対象版の自己参照を避けるため、検証対象のコミットと証跡の保存先を区別する。試験後に証跡を別コミットで保存する場合は、実際に検査した成果物版を明示して比較する。
done の宣言があっても、必要な依存が未完了または全完了条件の同じ版での報告が揃わなければ review_required とする。過去版のpassは自動継承しない。依存先がすべて recorded_done の提案・再開候補などを next_candidates として抽出する。blocked/paused/cancelled は自動で再開しない。判定は記録の整合性のみ。終了0は報告生成成功でありプロジェクトの完成ではない。要レビューの完了宣言がある場合は2、不正・検査不能は1。
## 制約
現在の全成果物版を単位とした保守的な判定。無関係な変更であっても版が変われば証跡再評価が必要になる。部分的な再検証や再利用の可否は forge_impact と意味レビューを併用する。実際の操作許可・保護要求・テストの真正性・ログの存在は別途確認する。結果から自動的な作業着手や状態更新はしない。依存関係は完全性を保証しない。正式採用・状態更新は対象の運用方針に従う。
