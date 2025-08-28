# Qwen Image Edit GUI — AI Fashion Model Prototype

Instagram 向けの **AIファッションモデル運用** を想定した画像編集ツールのプロトタイプです。  
Replicate API の **Qwen Image Edit** を呼び出し、アップロードした画像の服装をテキスト指示で差し替えます。  
フロントは **Gradio** で、ブラウザから直感的に操作できます。

## 特徴
- 画像の複数アップロード
- テキストプロンプトで服装差し替え
- 逐次処理のバッチ編集
- 実行結果の表示・保存（ZIP化は任意）
- Cloudflare Tunnel で外部共有デモが可能

## 技術スタック
- Python / Gradio
- Replicate API (Qwen Image Edit)
- Cloudflare Tunnel
- GitHub Actions（CI/CD 予定）

## 使い方
1. リポジトリを取得
   ```bash
   git clone https://github.com/USER/qwen-image-edit-gui.git
   cd qwen-image-edit-gui
2. 依存をインストール
   ```bash
   pip install -r requirements.txt
   
3. 環境変数を設定（Replicate API キー）
# Windows
set REPLICATE_API_TOKEN=your_api_token

# macOS / Linux
export REPLICATE_API_TOKEN=your_api_token
起動


python app.py
ブラウザで開く
http://127.0.0.1:7860

デモ
一時公開（任意）: Cloudflare Tunnel


cloudflared tunnel --url http://localhost:7860
出力される https://*.trycloudflare.com を共有してください。

ロードマップ
ComfyUI + IP-Adapter 連携で 参照画像による服装転写 を実現

Instagram 自動投稿パイプライン連携

EC / バーチャル試着への応用

ライセンス
MIT
