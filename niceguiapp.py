import os
import io
import time
import zipfile
import pathlib
from typing import List
from io import BytesIO

import requests
import replicate
from PIL import Image
from nicegui import ui, app

# ====== 設定 ======
MODEL_REF = 'qwen/qwen-image-edit'
API_TOKEN = os.getenv('REPLICATE_API_TOKEN')
if not API_TOKEN:
    raise RuntimeError('環境変数 REPLICATE_API_TOKEN を設定してください。（PowerShell: setx REPLICATE_API_TOKEN "r8_xxx"）')

BASE_DIR = pathlib.Path(__file__).parent.resolve()
DEFAULT_SAVE_DIR = BASE_DIR / 'outputs'
ASSETS_DIR = BASE_DIR / 'assets'    # 無くてもOK

# 静的ファイルのマウント（存在するときだけ）
if ASSETS_DIR.exists():
    app.add_static_files('/assets', str(ASSETS_DIR))

# 出力ディレクトリは常にマウント（初回実行時に自動生成）
DEFAULT_SAVE_DIR.mkdir(parents=True, exist_ok=True)
app.add_static_files('/outputs', str(DEFAULT_SAVE_DIR))


# ====== ユーティリティ ======
def ensure_dir(path_str: str | os.PathLike) -> pathlib.Path:
    p = pathlib.Path(path_str).expanduser().resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p

def pil_from_upload(file_bytes: bytes) -> Image.Image:
    return Image.open(BytesIO(file_bytes)).convert('RGB')

def download_image(url: str) -> Image.Image:
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    return Image.open(BytesIO(r.content)).convert('RGB')

def run_edit_one(local_path: pathlib.Path, prompt: str) -> List[str]:
    """1枚の画像をReplicateで編集し、出力URLのリストを返す"""
    with open(local_path, 'rb') as f:
        out = replicate.run(
            MODEL_REF,
            input={'image': f, 'prompt': prompt, 'output_quality': 80}
        )
    if not isinstance(out, list):
        out = [out]
    urls: List[str] = []
    for item in out:
        try:
            urls.append(item.url())
        except Exception:
            urls.append(str(item))
    return urls

def make_zip(zip_path: pathlib.Path, files: List[pathlib.Path]) -> pathlib.Path:
    with zipfile.ZipFile(zip_path, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            if f.exists():
                zf.write(f, arcname=f.name)
    return zip_path


# ====== UI 構築 ======
ui.colors(primary='#111827', secondary='#7c3aed', accent='#22d3ee')

with ui.header().classes('justify-between items-center px-4 py-2 bg-black text-white'):
    ui.label('Kisekae Studio').classes('text-lg font-semibold')
    ui.button(icon='info', on_click=lambda: ui.notify('Qwen Image Edit × Replicate', color='secondary')).props('flat round')

with ui.row().classes('w-full no-wrap'):
    # 左ペイン：設定
    with ui.card().classes('w-96 shrink-0 h-[calc(100vh-64px)] overflow-auto bg-gray-900 text-white'):
        ui.label('設定').classes('text-base font-semibold pb-2')

        prompt_in = ui.textarea(
            label='編集プロンプト',
            value=(
                'Replace her outfit with a beige knit sweater and wide black trousers. '
                'Keep hair, face, and background unchanged. Make the clothing fit naturally.'
            ),
        ).classes('w-full')

        ui.separator().classes('my-3 opacity-30')

        ui.label('対象画像（複数可）').classes('text-sm opacity-80')
        target_files = ui.upload(
            multiple=True,
            max_file_size=30*1024*1024,
            label='ここにドラッグ＆ドロップ / クリックして選択',
        ).classes('w-full mt-1')

        ui.separator().classes('my-3 opacity-30')

        ui.label('参照画像（任意・複数可）').classes('text-sm opacity-80')
        ref_files = ui.upload(
            multiple=True,
            max_file_size=30*1024*1024,
            label='（あるときだけ）参考にする服の写真を追加',
        ).classes('w-full mt-1')

        ui.separator().classes('my-3 opacity-30')

        save_toggle = ui.toggle(['保存しない', '保存する'], value='保存する').classes('mt-2')
        save_dir_in = ui.input('保存先フォルダ', value=str(DEFAULT_SAVE_DIR)).classes('w-full')
        make_zip_toggle = ui.checkbox('結果をZIPでまとめる', value=True)

        progress_bar = ui.linear_progress(show_value=True).props('striped').classes('w-full mt-2').bind_visibility_from(target_files, 'value')
        log_area = ui.textarea('ログ').classes('w-full h-44 mt-2').props('readonly')

        zip_link_row = ui.row().classes('mt-2')  # ZIPのダウンロードリンク置き場（後で上書き）

        async def run_pipeline():
            if not target_files.value:
                ui.notify('まず対象画像をアップロードしてね', color='negative')
                return

            # 参照があるならプロンプト補強
            final_prompt = prompt_in.value
            if ref_files.value:
                final_prompt += '\nUse the outfit from the reference image(s). Keep hair, face, and background unchanged.'

            # 保存先
            out_dir = ensure_dir(save_dir_in.value if save_toggle.value == '保存する' else DEFAULT_SAVE_DIR / 'temp')
            ts = time.strftime('%Y%m%d-%H%M%S')
            session_dir = ensure_dir(out_dir / ts)

            total = len(target_files.value)
            done = 0
            progress_bar.value = 0
            log_area.value = ''
            zip_link_row.clear()
            gallery_col.clear()
            await ui.update()

            saved_files: List[pathlib.Path] = []

            for i, f in enumerate(target_files.value):
                done += 1
                progress_bar.value = done / total
                progress_bar.set_text(f'{done}/{total}')

                # アップロード画像をローカルに保存
                input_path = session_dir / f'{ts}_{i:03d}_input.png'
                img = pil_from_upload(f.content)
                img.save(input_path)

                ui.notify(f'編集中: {input_path.name}', color='primary', position='top')

                try:
                    urls = run_edit_one(input_path, final_prompt)
                    if not urls:
                        raise RuntimeError('モデル出力が空でした')

                    # 代表1枚目
                    url = urls[0]
                    edited = download_image(url)

                    # 保存
                    if save_toggle.value == '保存する':
                        ext = pathlib.Path(url.split('?')[0]).suffix or '.webp'
                        out_path = session_dir / f'{ts}_{i:03d}_final{ext}'
                        edited.save(out_path)
                        saved_files.append(out_path)
                        log_area.value += f'Saved: {out_path}\n'

                    # ギャラリーに表示
                    with gallery_col:
                        with ui.card().classes('w-[360px] bg-gray-800'):
                            ui.image(edited).classes('rounded-lg')
                            ui.link('Open URL', url).classes('text-xs opacity-70')

                except Exception as e:
                    ui.notify(f'エラー: {e}', color='negative', position='top')
                    log_area.value += f'[ERROR] {input_path.name}: {e}\n'

            # ZIP生成（任意）
            if make_zip_toggle.value and saved_files:
                zip_path = session_dir / f'{ts}_results.zip'
                try:
                    make_zip(zip_path, saved_files)
                    # /outputs を静的配信しているのでリンクを貼れる
                    rel = zip_path.relative_to(DEFAULT_SAVE_DIR)
                    with zip_link_row:
                        ui.link('結果をZIPでダウンロード', f'/outputs/{rel.as_posix()}').classes('text-sm text-blue-600 underline')
                except Exception as e:
                    log_area.value += f'[ZIP ERROR] {e}\n'

            ui.notify('完了！', color='positive')

        ui.button('実行', on_click=run_pipeline).classes('w-full mt-3 bg-white text-black hover:bg-gray-200 font-semibold')

    # 右ペイン：ギャラリー
    with ui.element('div').classes('grow h-[calc(100vh-64px)] overflow-auto bg-gray-100 p-6'):
        ui.label('結果').classes('text-base font-semibold mb-3')
        gallery_col = ui.row().classes('gap-4')

ui.run(reload=False)  # 8080で起動
