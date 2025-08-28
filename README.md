Qwen Image Edit GUI (AI Fashion Model Prototype)
📖 概要

このプロジェクトは、Replicate API の Qwen Image Edit モデルを利用し、
入力画像の服装をテキスト指示に従って別スタイルに置き換える AI 画像編集ツールです。

目的は、Instagram での AI ファッションモデル運用に向けたプロトタイプ開発。
Gradio を用いて簡易 GUI を構築しており、誰でもブラウザから直感的に操作できます。

✨ 特徴

🖼️ 画像アップロード（複数対応）

📝 テキストプロンプトによる服装差し替え

🔄 逐次処理によるバッチ編集

📂 実行結果をブラウザ上に表示＆保存

🌐 Cloudflare Tunnel を利用した外部アクセス対応

🛠 技術スタック

フロントエンド / ツール

Python（メインロジック）

Gradio（GUI 構築）

バックエンド

Replicate API（Qwen Image Edit モデル呼び出し）

インフラ / 運用

Cloudflare Tunnel（デモ共有用）

GitHub Actions（CI/CD 管理予定）

🚀 実行方法

このリポジトリを clone

git clone https://github.com/ユーザー名/qwen-image-edit-gui.git
cd qwen-image-edit-gui


必要ライブラリをインストール

pip install -r requirements.txt


Replicate API キーを環境変数に設定

# Windows
set REPLICATE_API_TOKEN=your_api_token_here  

# macOS / Linux
export REPLICATE_API_TOKEN=your_api_token_here


アプリを起動

python app.py


ブラウザでアクセス

http://127.0.0.1:7860

🖼️ デモイメージ

（ここにスクリーンショットを追加）

🔮 今後の展望

ComfyUI を組み込んで 参照画像による服装転写 を実現

Instagram 自動投稿との連携

EC/ファッション分野での応用（試着システム、バーチャルモデル）

📜 ライセンス

MIT License
