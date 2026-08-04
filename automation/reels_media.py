"""Instagramリール用の縦型動画(画像+明るめのアンビエント音)をffmpegで生成する。

著作権のある音源ファイルを外部から取得することはできないため、
BGMはffmpegのlavfi(サイン波の長3和音+2段トレモロ+ビブラート)で
「明るく、抑揚のあるリズム」を数学的に合成する。3種類のプリセットを日付でローテーションする。
"""
import subprocess
from pathlib import Path

# 3種類のアンビエントプリセット(すべて長3和音+高音のきらめきで明るい響きにする)
AMBIENT_PRESETS = [
    {  # Cメジャー基調
        "freqs": [130.81, 164.81, 196.00, 523.25],
        "weights": "1 0.7 0.55 0.18",
        "tremolo_f1": 0.18, "tremolo_d1": 0.45,
        "tremolo_f2": 0.9, "tremolo_d2": 0.18,
    },
    {  # Gメジャー基調
        "freqs": [196.00, 246.94, 293.66, 587.33],
        "weights": "1 0.7 0.55 0.18",
        "tremolo_f1": 0.22, "tremolo_d1": 0.40,
        "tremolo_f2": 1.1, "tremolo_d2": 0.18,
    },
    {  # Fメジャー基調
        "freqs": [174.61, 220.00, 261.63, 698.46],
        "weights": "1 0.7 0.55 0.18",
        "tremolo_f1": 0.15, "tremolo_d1": 0.5,
        "tremolo_f2": 0.75, "tremolo_d2": 0.18,
    },
]

REEL_WIDTH = 1080
REEL_HEIGHT = 1920
FPS = 30


def _run_ffmpeg(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("=== ffmpegエラー ===")
        print(" ".join(cmd))
        print(result.stderr[-4000:])
        raise RuntimeError(f"ffmpegコマンドが失敗しました: {cmd[0]} ...")


def generate_ambient_track(preset_index: int, duration: int, out_path: Path) -> Path:
    """明るく抑揚のあるアンビエントトラックを合成して生成する。"""
    preset = AMBIENT_PRESETS[preset_index % len(AMBIENT_PRESETS)]
    inputs: list[str] = []
    for freq in preset["freqs"]:
        inputs += ["-f", "lavfi", "-i", f"sine=frequency={freq}:duration={duration}"]
    n = len(preset["freqs"])
    filter_complex = (
        f"amix=inputs={n}:duration=longest:weights={preset['weights']},"
        "lowpass=f=4200,"  # 高音域を残して明るい音色にする
        f"tremolo=f={preset['tremolo_f1']}:d={preset['tremolo_d1']},"  # ゆっくりした抑揚
        f"tremolo=f={preset['tremolo_f2']}:d={preset['tremolo_d2']},"  # 速めの揺れを重ねて表情を出す
        "vibrato=f=5:d=0.25,"
        "aecho=0.8:0.85:40:0.25,"
        "volume=0.5[a]"
    )
    _run_ffmpeg([
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[a]",
        str(out_path),
    ])
    return out_path


def build_reel_video(image_path: Path, audio_path: Path, out_path: Path, duration: int = 18) -> Path:
    """静止画をゆっくりズーム(Ken Burns風)させ、BGMを乗せた縦型リール動画を作る。"""
    silent_path = out_path.with_name(out_path.stem + "_silent.mp4")

    # 元画像(1024x1536想定)を9:16の土台まで拡大→中央クロップしてからズームさせる
    vf = (
        "scale=-2:2880,crop=1620:2880,"
        "zoompan=z='min(zoom+0.0007,1.15)':d=1:"
        "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"s={REEL_WIDTH}x{REEL_HEIGHT}:fps={FPS},format=yuv420p"
    )
    _run_ffmpeg([
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(image_path),
        "-vf", vf,
        "-t", str(duration),
        "-r", str(FPS),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(silent_path),
    ])

    _run_ffmpeg([
        "ffmpeg", "-y",
        "-i", str(silent_path),
        "-i", str(audio_path),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        str(out_path),
    ])
    silent_path.unlink(missing_ok=True)
    return out_path
