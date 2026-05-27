import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import yt_dlp

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT_DIR = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[1]
APP_DIR = ROOT_DIR
DEFAULT_DOWNLOAD_DIR = str(Path.home() / "Downloads")
HISTORY_FILE = APP_DIR / "history.json"
STATS_FILE = APP_DIR / "stats.json"


def get_ffmpeg_dir():
    candidates = [ROOT_DIR]
    if getattr(sys, "frozen", False):
        candidates += [Path(sys.executable).parent, Path(sys.executable).parent / "_internal"]
    for path in candidates:
        if (path / "ffmpeg.exe").exists():
            return str(path)
    return None


FFMPEG_DIR = get_ffmpeg_dir()


def clean_url(url):
    import urllib.parse as up

    url = url.strip()
    parsed = up.urlparse(url)
    if "/shorts/" in parsed.path:
        video_id = parsed.path.split("/shorts/")[-1].split("/")[0].split("?")[0]
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"
    params = up.parse_qs(parsed.query)
    if "v" in params:
        return f"https://www.youtube.com/watch?v={params['v'][0]}"
    return url


def get_video_info(url):
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "socket_timeout": 15,
        "retries": 2,
        "nocheckcertificate": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)


def build_format_list(info, mode):
    if mode == "mp3":
        return [("320k  EN YUKSEK", "320"), ("256k  YUKSEK", "256"), ("192k  ORTA", "192"), ("128k  DUSUK", "128")]
    if mode == "m4a":
        return [("256k  EN YUKSEK", "256"), ("192k  YUKSEK", "192"), ("128k  ORTA", "128")]

    formats = info.get("formats", [])
    video_formats = {}
    for item in formats:
        height = item.get("height")
        format_id = item.get("format_id", "")
        vcodec = item.get("vcodec") or "none"
        if not height or not format_id or vcodec == "none":
            continue
        label = f"{height}p"
        if label not in video_formats or vcodec not in ("none", "unknown_video"):
            video_formats[label] = format_id

    if not video_formats:
        for item in formats:
            height = item.get("height")
            format_id = item.get("format_id", "")
            if height and format_id:
                video_formats.setdefault(f"{height}p", format_id)

    tags = {2160: "4K", 1440: "2K", 1080: "FHD", 720: "HD", 480: "SD", 360: "LOW", 240: "VLOW", 144: "MIN"}
    results = []
    for height in [2160, 1440, 1080, 720, 480, 360, 240, 144]:
        label = f"{height}p"
        if label in video_formats:
            results.append((f"{label}  {tags.get(height, label)}", video_formats[label]))
    standard = {2160, 1440, 1080, 720, 480, 360, 240, 144}
    for item in formats:
        height = item.get("height")
        format_id = item.get("format_id", "")
        vcodec = item.get("vcodec") or "none"
        if height and height not in standard and format_id and vcodec != "none":
            results.append((f"{height}p  OZEL", format_id))
    return results


def load_history():
    try:
        if HISTORY_FILE.exists():
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return []


def save_history(records):
    try:
        HISTORY_FILE.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def load_stats_file():
    try:
        if STATS_FILE.exists():
            return json.loads(STATS_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"total_count": 0, "total_bytes": 0, "by_format": {"mp3": 0, "mp4": 0, "m4a": 0}}


def save_stats_file(stats):
    try:
        STATS_FILE.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def emit(event, **payload):
    print(json.dumps({"event": event, **payload}, ensure_ascii=False), flush=True)


def fmt_bytes(value):
    if value < 1024:
        return f"{value}B"
    if value < 1024**2:
        return f"{value / 1024:.1f}KB"
    if value < 1024**3:
        return f"{value / 1024**2:.1f}MB"
    return f"{value / 1024**3:.2f}GB"


def seconds_to_hms(seconds):
    if not seconds:
        return "?"
    hours, rem = divmod(int(seconds), 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


def parse_time(value):
    value = (value or "").strip()
    if not value:
        return None
    parts = value.split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        return int(parts[0])
    except ValueError:
        return None


def estimate_size(label, mode, duration):
    if not duration:
        return ""
    bitrate_map = {
        "320k": 320,
        "256k": 256,
        "192k": 192,
        "128k": 128,
        "4K": 25000,
        "2K": 12000,
        "1080p": 4000,
        "720p": 2000,
        "480p": 1000,
        "360p": 600,
        "240p": 350,
        "144p": 150,
    }
    bitrate = next((v for k, v in bitrate_map.items() if k in label), None)
    if bitrate is None:
        return ""
    size = int((bitrate * 1000 / 8) * duration)
    return fmt_bytes(size)


def update_stats(mode, filesize=0):
    stats = load_stats_file()
    stats["total_count"] = stats.get("total_count", 0) + 1
    stats["total_bytes"] = stats.get("total_bytes", 0) + filesize
    by_format = stats.setdefault("by_format", {"mp3": 0, "mp4": 0, "m4a": 0})
    by_format[mode] = by_format.get(mode, 0) + 1
    save_stats_file(stats)
    return stats


def add_history(title, mode, quality, url):
    records = load_history()
    record = {
        "title": title,
        "mode": mode,
        "quality": quality,
        "url": url,
        "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
    }
    records.append(record)
    save_history(records)
    return record


def choose_format(formats, preferred_label):
    if not formats:
        return "", ""
    if preferred_label:
        exact = next((item for item in formats if item[0] == preferred_label), None)
        if exact:
            return exact
        prefix = preferred_label.split("  ")[0]
        matched = next((item for item in formats if item[0].startswith(prefix)), None)
        if matched:
            return matched
    return formats[0]


def build_ydl_opts(mode, fmt_id, outdir, clip_start=None, clip_end=None, subtitle=False, sub_lang="tr"):
    outtmpl = os.path.join(outdir, "%(title)s.%(ext)s")
    base = {
        "quiet": True,
        "no_warnings": True,
        "outtmpl": outtmpl,
        "progress_hooks": [progress_hook],
        "socket_timeout": 15,
        "retries": 3,
        "nocheckcertificate": True,
    }
    if FFMPEG_DIR:
        base["ffmpeg_location"] = FFMPEG_DIR

    pp_args = {}
    if clip_start is not None or clip_end is not None:
        start_args = ["-ss", str(clip_start)] if clip_start is not None else []
        end_args = ["-to", str(clip_end)] if clip_end is not None else []
        pp_args = {"default": start_args + end_args}

    if subtitle:
        base["writesubtitles"] = True
        base["writeautomaticsub"] = True
        base["subtitleslangs"] = [sub_lang, "en"]
        base["subtitlesformat"] = "srt"

    if mode == "mp3":
        opts = {
            **base,
            "format": "bestaudio/best",
            "postprocessors": [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": fmt_id}
            ],
        }
        if pp_args:
            opts["postprocessor_args"] = pp_args
        return opts

    if mode == "m4a":
        opts = {
            **base,
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "postprocessors": [
                {"key": "FFmpegExtractAudio", "preferredcodec": "m4a", "preferredquality": fmt_id}
            ],
        }
        if pp_args:
            opts["postprocessor_args"] = pp_args
        return opts

    fmt_str = f"{fmt_id}+bestaudio[ext=m4a]/{fmt_id}+bestaudio/bestvideo[height<={fmt_id}]+bestaudio/best"
    merger = ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k"]
    opts_pp = {"merger": merger, **pp_args} if pp_args else {"merger": merger}
    return {
        **base,
        "format": fmt_str,
        "merge_output_format": "mp4",
        "postprocessors": [
            {"key": "FFmpegVideoConvertor", "preferedformat": "mp4"},
            {"key": "FFmpegMetadata"},
        ],
        "postprocessor_args": opts_pp,
    }


def progress_hook(data):
    status = data.get("status")
    if status == "downloading":
        total = data.get("total_bytes") or data.get("total_bytes_estimate", 0)
        downloaded = data.get("downloaded_bytes", 0)
        speed = data.get("speed", 0) or 0
        eta = data.get("eta", 0) or 0
        percent = (downloaded / total) if total else 0
        emit(
            "progress",
            progress=percent,
            percent=f"{percent * 100:.0f}%",
            speed=f"{speed / 1024 / 1024:.1f} MB/s" if speed else "",
            eta=eta,
        )
    elif status == "finished":
        emit("progress", progress=0.99, percent="99%", status="Isleniyor")


def command_analyze(payload):
    url = clean_url(payload.get("url", ""))
    mode = payload.get("mode", "mp4")
    emit("status", message="Video analiz ediliyor")
    info = get_video_info(url)
    formats = build_format_list(info, mode)
    qualities = [{"label": label, "id": fmt_id} for label, fmt_id in formats]
    selected = qualities[0]["label"] if qualities else ""
    emit(
        "result",
        url=url,
        id=info.get("id", ""),
        title=info.get("title", "Bilinmiyor"),
        channel=info.get("uploader", "?"),
        duration=seconds_to_hms(info.get("duration")),
        durationSeconds=info.get("duration", 0) or 0,
        views=info.get("view_count", 0) or 0,
        thumbnail=info.get("thumbnail", ""),
        qualities=qualities,
        selectedQuality=selected,
        estimatedSize=estimate_size(selected, mode, info.get("duration", 0) or 0),
    )


def command_download(payload):
    url = clean_url(payload.get("url", ""))
    mode = payload.get("mode", "mp4")
    outdir = payload.get("outdir") or DEFAULT_DOWNLOAD_DIR
    quality_label = payload.get("quality", "")
    os.makedirs(outdir, exist_ok=True)

    emit("status", message="Video bilgisi aliniyor")
    info = get_video_info(url)
    formats = build_format_list(info, mode)
    selected_label, fmt_id = choose_format(formats, quality_label)
    if not fmt_id:
        raise RuntimeError("Uygun format bulunamadi.")

    opts = build_ydl_opts(
        mode,
        fmt_id,
        outdir,
        clip_start=parse_time(payload.get("clipStart", "")),
        clip_end=parse_time(payload.get("clipEnd", "")),
        subtitle=bool(payload.get("subtitle", False)),
        sub_lang=payload.get("subLang", "tr"),
    )
    emit("status", message=f"Indirme basladi: {mode.upper()} / {selected_label}")
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])

    record = add_history(info.get("title", ""), mode, selected_label, url)
    stats = update_stats(mode)
    emit("done", message="Indirme tamamlandi", record=record, stats=stats)


def command_history(_payload):
    emit("result", records=load_history())


def command_stats(_payload):
    emit("result", stats=load_stats_file())


COMMANDS = {
    "analyze": command_analyze,
    "download": command_download,
    "history": command_history,
    "stats": command_stats,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=COMMANDS.keys())
    parser.add_argument("--payload", default="{}")
    args = parser.parse_args()
    try:
        payload = json.loads(args.payload)
        COMMANDS[args.command](payload)
    except Exception as exc:
        emit("error", message=str(exc))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
