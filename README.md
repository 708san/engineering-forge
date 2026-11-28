# Engineering Forge

AIがプロダクト固有の開発体制を設計・生成・改善する開発基盤。従来の設計名は Development Harness。

**状態: v0.17-dev（開発中、正式リリース・受入未完了）。**

## 利用開始
**通常はURLと構想だけでよい。補助コマンドや共通レコードの採用は任意。** 開発版を使う場合は変更ブランチまたは固定コミットを指定する。mainは未統合。

[初めて使う（ChatGPT・Codex共通）](bootstrap/quickstart.md) ｜ [実機試験手順](evaluation/first-use.md)

[START.md](START.md) を AI に読ませ、自由記述の構想または既存リポジトリを伝える。AI が必要な方法、役割、品質基準、技術・開発環境を考案する。既存分類や固定カタログへの一致を要求しない。

対象側に生成するファイルは自己完結させる。リポジトリ参照のみで Skills のインストールや権限の付与が行われるわけではない。

## 最初の実装
プレビューは Python 3.11 以上、標準ライブラリのみ。別々の既存ディレクトリを指定する。

    python3 forge_preview.py CANDIDATE TARGET

候補ファイルと対象の内容を比較し、add / unchanged / conflict を JSON で標準出力する。終了コードは 0=競合なし、2=競合あり、1=検査不能。対象へ書き込まない。未指定の対象ファイルは削除しない。ローカルの信頼できる静止した作業領域を想定し、同時編集や敵対的なファイルシステムに対する保証はない。適用・承認・内容の安全性・意味的妥当性を証明しない。

## 設計資産
- requirements.md: 48要求の現行草案（v0.4の表記を維持）
- detail.md / generative-architecture.md / architect-v0.5.md: 詳細設計
- .agents/skills/: 初期の8能力
- bootstrap/contract.md: 導入契約
- evaluation-v0.5.md / evaluation.md: 受入・比較評価仕様（未実施）

この初期登録は v0.6 の主要文書と Skills を移行したもの。共通レコードスキーマと一部fixtureはv0.13で復元済み。旧版履歴・設計試験一式などは未移行。正式な仕様ベースラインとしての承認、独立監査、Codex 実機の Skills 読み込み、自動生成・適用の実証は未完了。公開リポジトリに秘密情報や私的な会話原文を含めない。ライセンス未決定。

## ChatGPT・Codexからの利用
[共通の立ち上げ・継続開発手順](bootstrap/portable-project.md) を参照。AIが候補を生成する方式で、固定分類のジェネレーターや自動適用エンジンではない。

## 候補の構造検証（任意）
Python 3.11以上の環境で、仮想環境内に依存を導入する。

    python3 -m pip install -r requirements-validator.txt
    python3 forge_validate.py examples/portable-candidate/blueprint.json --baseline examples/portable-candidate/baseline.example.json
    python3 -m unittest discover -s tests -v

初回提案には --new-proposal を使う。正式基準がある場合は候補とは別に管理した --baseline を指定する。比較元の真正性は検証しない。構造・参照・必須成果の検査のみで、意味・品質・権限・承認・実環境の検証を代替しない。終了コードは 0=構造検査成功、2=不適合、1=検査不能（依存未導入も失敗）。公開例は校正用データであり、新規AI生成実験ではない。

## 継続開発の引き継ぎ
[引き継ぎ検査](bootstrap/handoff.md) は任意のプロジェクト内ファイルの内容変化を検出する。対象の運用には必須ではない。`examples/uncertain-order/` に独立動作する試作例を収録。独立AIへの引き継ぎは未検証。

## 新規導入・更新と変更影響
[Git統合ブランチへの導入](bootstrap/integration.md) と [変更影響検査](bootstrap/change-impact.md) を追加。ローカルでの任意補助機能であり、GitHubへの自動Pushや自動マージ、保護要求の承認を行わない。基盤本体の試験は Git と Python 3.11以上、requirements-validator.txt の依存を準備して `python3 -B -m unittest discover -s tests -v`。ChatGPTが実行できない場合は候補・計画・未実施事項を渡す。

## 共通コマンド（任意）
`python3 forge.py doctor` でローカル環境の観測結果を取得し、`python3 forge.py --help` で補助コマンドを確認できる。実行可能ファイルが見つかったことと、実際の利用権限・Skills読込・準備完了は別であり、doctorは後者を未検証と表示する。GitHub ActionsはLinux/macOS・Python 3.11/3.13の自動試験設定。

## 配布・知識の再利用
[任意の共通プラグイン配布](bootstrap/distribution.md)（`python3 -B forge.py pack --ref HEAD --output engineering-forge.zip`）と[知識の再利用](knowledge/README.md)を追加。パッケージ生成はインストールや公開を意味しない。既存のURL参照も利用可能。v0.10のCI成功ログと取得コードに矛盾を発見し検証器の差集合演算を修正した。原因は未解明。

[実行環境別エージェント候補](bootstrap/agent-adapters.md) を追加。`forge.py agents BLUEPRINT.json AGENT-SPEC.json` はAIが考案した役割をCodex用TOMLとChatGPT向け作業契約へ変換する（任意）。生成のみで起動・権限付与は行わない。

## タスクと証跡の整合性・評価
[進捗・証跡検査](bootstrap/progress.md)（forge.py progress）は宣言した依存関係と版別の観測記録を照合する。承認や実行の証明ではない。比較評価用の[公開校正ケース](evaluation/calibration-v0.12.md)と[試行記録契約](evaluation/run-record.md)を追加（正式比較未実施）。

## 共通記録とプロジェクト固有形式
[共通情報モデル](bootstrap/records.md)（forge.py records）は復元した29種の旧仕様と任意の名前空間付き拡張を検査する。既存の形式を無理に置き換えず必要な場合だけ利用する。未知拡張は保持し未検証とする。

共通レコードの保護条件・Roleの権限範囲を独立した旧基準と比較する任意機能 `forge.py guard` を追加。承認の真正性や実効的権限制御を保証しない。

## 正本に基づく開発の再開
[作業契約・セッション検査](bootstrap/session.md)（forge.py session）は共通レコードから候補と作業契約を導出し、依存・版・証跡・宣言上の操作範囲を照合する。実行・承認はしない。既存の課題管理を利用してもよい。

`forge.py baseline PROJECT_ROOT MANIFEST` は基準の固定レコード集合の内容指紋を計算する。`session --target CODE_WORKTREE` は記録保存先とは別のコード作業領域のHEADを観測できる。

[開発体制の改善試行](bootstrap/adaptation.md)を追加。任意の trial コマンドは事前定義の指標と観測を比較する。採用・承認は別工程。

## 完成判定
[正式受入索引](evaluation/acceptance-index.md) は従来56条件と導入専用8条件を区別する。単体試験と正式受入、実機検証、独立比較を別扱いにする。未実施の条件は合格としない。

[正式版への残作業・独立監査の入口](evaluation/release-readiness.md)。

[複合案件の公開校正試作 CAL-02](examples/calibration-hearing/AGENTS.md) と [自己適用記録](evaluation/calibration-hearing-observation.md)。実認証・ネットワーク・個人情報処理を備えた製品ではない。
