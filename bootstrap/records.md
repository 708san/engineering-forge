# 共通情報モデルと独自形式の任意検査（v0.13-dev）
v0.6設計アーカイブの record.schema.json / project.schema.json / example-response-map.schema.json と fixtures/project.json / fixtures/records.json を原本と同一内容で復元した。29の論理種別は共通情報の意味を区別するためのもので、全種類の記録・文書を作る義務ではない。製品分類、方法、エージェント数を決めるものでもない。小規模なら既存の文書と手動追跡を維持する。
`python3 -B forge.py records PROJECT_ROOT RELATIVE_MANIFEST.json` はプロジェクト相対パスのmanifestと記録配列を検査する。例: `python3 -B forge.py records . fixtures/project.json`。Python 3.11+、requirements-validator.txt の依存が必要。
manifest は正本の配置、参照する基準版、方針・環境、拡張登録を持つ。レコードは一意のID・版・来歴・状態・責任・関係・本文または本文参照を持つ。本文参照の内容ハッシュ、関係・型付き参照、重複版、複数のactive版、実行依存と階層の循環を検査する。版なし参照は唯一のactive版に解決し、版指定は該当版を参照する。Evidenceの別基準版や環境差などは再確認対象にする。結果は報告された証跡で、実行を認証しない。
## 拡張
任意の `x.<namespace>.<kind>` と版を定義し、JSON Schemaをプロジェクト内に保存し、manifestのextension_registryにtype_id/version/schema_path/sha256を登録する。独自形式を使うレコードは extension_schema_ref で型と版を指定する。登録済みのスキーマについてハッシュ、構文、データを検査する。未知版・未登録形式はそのまま保持して未検証と出力する。ファイルは変更しない。
初期実装は安全側に制限したローカル宣言的JSON Schemaの部分集合のみ。外部参照・動的参照・カスタムキーワードやコードを実行しない。全JSON Schemaの機能には対応していない。正規表現等は信頼済み入力前提で、悪意ある巨大入力に対する資源制限は未実装。外部資料を権限の根拠としない。拡張ペイロードのキーを権限・承認・実行命令として扱わない。
終了0は実装範囲の構造検査が成功、2は未登録拡張あり、1は不正・検査不能。いずれも正式受入や品質の合格ではない。本文アンカー、基準スナップショットの真正性、生成管理出力、Practice.definition_refの解決、実行強制、履歴の完全性、保護変更の承認は別途検査・レビューが必要。旧設計の全資産移行はまだ完了していない。
