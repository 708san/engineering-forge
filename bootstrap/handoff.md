# 任意の引き継ぎ検査（v0.9-dev）
引き継ぎは対象内の正本・開発入口・次の作業・保留事項を保存する。ファイル名や役割数・開発方法を固定しない。AIがプロジェクトに合わせて必要な文脈ファイルを選ぶ。不要な機密情報を入れない。
## コマンド
Python 3.11以上、標準ライブラリのみ。基盤を取得している作業環境で実行する。

    python3 forge_handoff.py snapshot examples/uncertain-order examples/uncertain-order/handoff-spec.json
    python3 forge_handoff.py verify examples/uncertain-order examples/uncertain-order/handoff-manifest.json

snapshot は標準出力に JSON を出す。保存する場合は既存の証跡や入力文書を上書きしないパスを使用する。verify は一致なら0、内容変化なら2、欠落・不正形式・検査不能なら1で終了する。検査対象への書込はしない。
spec は project, forge_commit, target_commit, entrypoint, context, next_actions, blockers を持つ。コミットは確認した40桁のSHAまたはnull。context は実ファイルへのプロジェクト相対POSIXパスの配列、entrypoint はその一つ。next_actions と blockers は自由記述。manifest は spec と各ファイルのSHA-256を含む。自分自身をcontextに含めない。
## 再開
1. 対象のコミット・未コミット差分・現在の権限を実際に確認する。
2. manifest を以前の状態の参照として検査し、変化・欠落があれば原因を確認。人間の編集を保持する。manifest を更新するだけで過去のテストを有効とみなさない。
3. 対象の入口と正式仕様、必要な資料を読んで次の作業を判断する。記載された作業は提案であり、権限・承認・検証結果の証拠ではない。
4. 作業終了後、必要な正本・状態・証跡を更新する。新たなスナップショットは以前の証跡と区別する。
## 限界
静止した信頼できるローカル作業領域のみ。選択されたファイルの内容比較であり、全ツリー、Git HEAD、署名、manifest自体の真正性、競合編集、権限、テスト合格、外部参照を含む完全な自己完結性の検証ではない。未列挙ファイルの変更は検出しない。対象の基本運用に本ツールは必須ではない。ChatGPTの読み取り専用環境ではコマンド実行済みと主張せず、参照先と状態を手動で照合する。
## 公開実験例
examples/uncertain-order はこのチャットのAIが構想・設計・試作を行った合成例。単独ディレクトリに複製して標準ライブラリだけでテストを実施した。独立AIへの引き継ぎ実験ではない。コピー用の固定テンプレートではない。
