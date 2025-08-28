import os
import time
import pathlib
import requests
import replicate
import gradio as gr

# PowerShell で事前に:
#   setx REPLICATE_API_TOKEN "r8_xxxxxxxxxxxxxxxxx"
API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
if not API_TOKEN:
    raise RuntimeError("環境変数 REPLICATE_API_TOKEN を設定してください。")

MODEL_REF = "qwen/qwen-image-edit"  # Version ID は不要

# 保存フォルダ作成
def _ensure_dir(d: str) -> str:
    p = pathlib.Path(d).expanduser().resolve()
    p.mkdir(parents=True, exist_ok=True)
    return str(p)

# 画像を保存
def _download(url: str, dst_path: pathlib.Path):
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    dst_path.write_bytes(r.content)
    return str(dst_path)

def edit_images(
    target_paths,            # 着せ替え対象（複数）
    prompt,
    ref_paths,               # 参照画像（任意）
    autosave,                # 自動保存ON/OFF
    save_dir,                # 保存先
    progress=gr.Progress(track_tqdm=True),
):
    if not target_paths:
        raise gr.Error("画像をアップロードしてください。")

    # 参照画像があるときはプロンプトに追記（直接渡せないのでテキストで補助）
    final_prompt = prompt
    if ref_paths:
        final_prompt += "\nUse the outfit from the reference image(s). Keep hair, face, and background unchanged."

    # 保存先フォルダ準備
    save_dir = _ensure_dir(save_dir if save_dir else "outputs")
    ts = time.strftime("%Y%m%d-%H%M%S")

    urls_for_gallery, logs = [], []

    n = len(target_paths)
    for i, p in enumerate(target_paths):
        progress(i / n if n else 0.0,
                 desc=f"Processing {i+1}/{n}: {os.path.basename(p)}")

        with open(p, "rb") as f:
            out = replicate.run(
                MODEL_REF,
                input={"image": f, "prompt": final_prompt, "output_quality": 80}
            )

        if not isinstance(out, list):
            out = [out]

        for j, item in enumerate(out):
            try:
                url = item.url()   # SDKオブジェクトのとき
            except Exception:
                url = str(item)    # すでにURL文字列のとき

            urls_for_gallery.append(url)

            if autosave:
                ext = pathlib.Path(url.split("?")[0]).suffix or ".webp"
                dst = pathlib.Path(save_dir) / f"{ts}_{i:03d}_{j:02d}{ext}"
                try:
                    _download(url, dst)
                    logs.append(f"Saved: {dst}")
                except Exception as e:
                    logs.append(f"[SAVE ERROR] {dst.name}: {e}")

    progress(1.0, desc="Done")
    return urls_for_gallery, ("\n".join(logs) if logs else "Done.")

# GUI
with gr.Blocks(title="Qwen Image Edit Batch GUI") as demo:
    gr.Markdown("### Qwen Image Edit Batch GUI\nローカル画像を複数アップロードして一括編集（Replicate実行）")

    with gr.Row():
        target_in = gr.File(
            label="着せ替え対象の画像（複数可）",
            file_types=[".png", ".jpg", ".jpeg", ".webp"],
            type="filepath",
            file_count="multiple"
        )
        ref_in = gr.File(
            label="参照画像（任意・複数可）",
            file_types=[".png", ".jpg", ".jpeg", ".webp"],
            type="filepath",
            file_count="multiple"
        )

    prompt_in = gr.Textbox(
        label="編集プロンプト",
        value=(
            "Replace her outfit with a beige knit sweater and wide black trousers. "
            "Keep hair, face, and background unchanged. Make the clothing fit naturally."
        ),
        lines=3
    )

    with gr.Row():
        autosave_in = gr.Checkbox(label="出力を自動保存する", value=True)
        save_dir_in = gr.Textbox(label="保存先フォルダ", value="outputs")

    run_btn = gr.Button("実行", variant="primary")
    gallery_out = gr.Gallery(label="生成結果", columns=2, rows=2, show_label=True)
    log_out = gr.Textbox(label="ログ", value="", interactive=False)

    run_btn.click(
        fn=edit_images,
        inputs=[target_in, prompt_in, ref_in, autosave_in, save_dir_in],
        outputs=[gallery_out, log_out]
    )

if __name__ == "__main__":
    demo.launch()
