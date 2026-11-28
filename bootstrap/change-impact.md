# 継続開発の変更影響検査（v0.10-dev）
プロジェクト固有の仕様・方法・タスク・検証証跡・その他任意の種類を記録として表し、依存先が変化した際に再確認候補を抽出する。記録の種類は自由記述であり、製品分類は不要。小規模案件では手動確認でもよい。
## 入力
対象の以前の handoff-manifest.json（bootstrap/handoff.md）、以前にレビューされた依存関係 graph.json。graph の records 配列内に id（重複なしの文字列）、kind（任意の種類）、files（対象の相対パス配列）、depends_on（依存先record IDの配列）を記述する。証跡が実装に、実装が要求に依存するなら、要求の変更が証跡の再確認へ伝播する。
    python3 forge_impact.py TARGET MANIFEST.json GRAPH.json
    python3 forge_impact.py TARGET MANIFEST.json GRAPH.json --changed-id REQUIREMENT-01
明示したIDや観測されたファイルの変更から、宣言済み依存先を逆方向に辿る。循環は無限に処理しない。出力は direct、affected（review_required）、unmapped_changes（記録との紐付けなし）、unwatched_dependencies（以前のmanifestに未列挙）を含む。変更・確認対象ありは終了コード2、検出なし0、欠落・不正形式・検査不能1。
## 運用
以前のgraphとmanifestを基準として保存する。候補AIが都合よくリンクを削除したgraphに置き換えて過去の証跡を有効扱いしない。影響結果は作業計画・必要な再試験・変更提案・保留の材料であり、仕様の変更やテスト結果の上書きは行わない。人間が追加した依存関係や意味的な影響も検討する。関係のない作業まで一律に停止しない。
記録やファイルの完全性・真正性・意味・権限は未検証。未列挙ファイルの変更、新規作成、記録されていない依存関係は網羅できない。ファイル欠落は検査不能として停止し、別途調査する。適用・再検証を実行した後に、新しい基準と証跡を保存する。
