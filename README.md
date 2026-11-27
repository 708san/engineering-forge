# Engineering Forge

AIがプロダクト固有の開発体制を設計・生成・改善する開発基盤。従来の設計名は Development Harness。

**状態: v0.7-dev（開発中、正式リリース・受入未完了）。**

## 利用開始
[START.md](START.md) を AI に読ませ、自由記述の構想または既存リポジトリを伝える。AI が必要な方法、役割、品質基準、技術・開発環境を考案する。既存分類や固定カタログへの一致を要求しない。

対象側に生成するファイルは自己完結させる。リポジトリ参照のみで Skills のインストールや権限の付与が行われるわけではない。

## 最初の実装
Python 3.11 以上、標準ライブラリのみ。別々の既存ディレクトリを指定する。

    python3 forge_preview.py CANDIDATE TARGET
    python3 -m unittest discover -s tests -v

候補ファイルと対象の内容を比較し、add / unchanged / conflict を JSON で標準出力する。終了コードは 0=競合なし、2=競合あり、1=検査不能。対象へ書き込まない。未指定の対象ファイルは削除しない。ローカルの信頼できる静止した作業領域を想定し、同時編集や敵対的なファイルシステムに対する保証はない。適用・承認・内容の安全性・意味的妥当性を証明しない。

## 設計資産
- requirements.md: 48要求の現行草案（v0.4の表記を維持）
- detail.md / generative-architecture.md / architect-v0.5.md: 詳細設計
- .agents/skills/: 初期の8能力
- bootstrap/contract.md: 導入契約
- evaluation-v0.5.md / evaluation.md: 受入・比較評価仕様（未実施）

この初期登録は v0.6 の主要文書と Skills を移行したもの。旧版履歴、完全なレコードスキーマ、設計試験・fixture 一式はまだ別の v0.6 アーカイブにある。正式な仕様ベースラインとしての承認、独立監査、Codex 実機の Skills 読み込み、自動生成・適用の実証は未完了。公開リポジトリに秘密情報や私的な会話原文を含めない。ライセンス未決定。
