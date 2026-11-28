# 配布方法（v0.11-dev）
## URL参照（既存の標準）
ChatGPT、Codexにリポジトリと START.md を示す。書込・コマンド・ネイティブSkillの利用能力は環境ごとに確認する。これが基本であり、プラグインは必須ではない。
## 任意の配布用プラグイン
OpenAIの公開仕様にある portable Agent Plugins の skill-only 構造を採用する（公式資料 https://developers.openai.com/plugins/build/plugins 、https://developers.openai.com/plugins/concepts/skills ）。インストール可否・審査・利用可能な画面は未検証。
信頼できる基盤のGitチェックアウトから次を実行する（Python 3.11以上、Git）。
    python3 -B forge.py pack --ref HEAD --output engineering-forge.zip
対象の固定コミットを指定することもできる。生成物は新規ZIPのみ。コミットから明示した基盤文書・Skillsを選んで同梱し、未コミット編集、対象プロジェクト、履歴、認証情報、実行スクリプトを含めない。選択された文書に機密がないことは別途レビューする。既存ファイルを上書きしない。
ZIPのrootに plugin.json と skills/engineering-forge/SKILL.md があり、同梱文書は skills/engineering-forge/references/ にある。SOURCE.json は取得元コミットと内容ハッシュを記録する（署名ではない）。複数の元Skillを参照資料として同梱し、ネイティブに有効なのは単一入口を想定する。プロジェクトごとの専用Skillやエージェントを一律生成しない。
ホストのローカル/リポジトリマーケットプレイス等の利用可能な導入方式に従い、必要なら展開して試用する。公開提出、マーケットプレイス登録、インストール、権限変更はこのツールでは行わない。ネイティブ読込と実際の開発は別途実機試験。ホストが対応しない場合はURL参照を使う。
