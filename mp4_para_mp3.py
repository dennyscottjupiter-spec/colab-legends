# ---
# purpose: Converte MP4 (ou qualquer video) em MP3 mono 16 kHz otimizado para transcricao
# exports: converter(), achar_ffmpeg(), main()
# depends: ffmpeg no PATH ou pacote imageio-ffmpeg (fallback automatico)
# gotcha: saida sempre mono 16 kHz 64 kbps - e o formato que o Whisper usa internamente
# ---
"""Uso:
    python3 mp4_para_mp3.py video.mp4            # um arquivo
    python3 mp4_para_mp3.py C:\\pasta\\videos     # todos os .mp4/.mkv/.mov da pasta
    python3 mp4_para_mp3.py                      # todos os videos da pasta atual
"""
import shutil
import subprocess
import sys
from pathlib import Path

EXTENSOES = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v"}


def achar_ffmpeg() -> str:
    """ffmpeg do PATH; se nao houver, o binario que vem com imageio-ffmpeg."""
    caminho = shutil.which("ffmpeg")
    if caminho:
        return caminho
    try:
        import imageio_ffmpeg
    except ImportError:
        sys.exit("ffmpeg nao encontrado. Rode: python3 -m pip install imageio-ffmpeg")
    return imageio_ffmpeg.get_ffmpeg_exe()


def converter(video: Path, ffmpeg: str) -> Path | None:
    """Gera o .mp3 ao lado do video; None se o ffmpeg recusar o arquivo."""
    saida = video.with_suffix(".mp3")
    resultado = subprocess.run(
        [
            ffmpeg, "-y", "-loglevel", "error",
            "-i", str(video),
            "-vn",                    # descarta o video
            "-ac", "1",               # mono
            "-ar", "16000",           # 16 kHz
            "-c:a", "libmp3lame",
            "-b:a", "64k",
            str(saida),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if resultado.returncode != 0:
        saida.unlink(missing_ok=True)
        erro = (resultado.stderr or "").strip().splitlines()
        print("FALHOU (arquivo sem audio ou corrompido)")
        if erro:
            print(f"   ffmpeg: {erro[-1]}")
        return None
    return saida


def alvos(args: list[str]) -> list[Path]:
    if not args:
        return sorted(p for p in Path.cwd().iterdir() if p.suffix.lower() in EXTENSOES)
    encontrados = []
    for arg in args:
        alvo = Path(arg)
        if alvo.is_dir():
            encontrados += sorted(p for p in alvo.iterdir() if p.suffix.lower() in EXTENSOES)
        elif alvo.is_file():
            encontrados.append(alvo)
        else:
            print(f"ignorado (nao existe): {alvo}")
    return encontrados


def main() -> None:
    videos = alvos(sys.argv[1:])
    if not videos:
        sys.exit("Nenhum video encontrado. Passe um arquivo ou uma pasta como argumento.")
    ffmpeg = achar_ffmpeg()
    print(f"ffmpeg: {ffmpeg}\n")
    feitos, falhas = 0, 0
    for video in videos:
        print(f"-> {video.name}", end=" ", flush=True)
        if video.with_suffix(".mp3").exists():
            print("ja convertido (pulei)")
            continue
        mp3 = converter(video, ffmpeg)
        if mp3 is None:
            falhas += 1
            continue
        feitos += 1
        print(f"OK  ({mp3.stat().st_size / 1e6:.1f} MB)  {mp3}")
    print(f"\n{feitos} arquivo(s) convertido(s). Suba o .mp3 no notebook do Colab.")
    if falhas:
        print(f"{falhas} arquivo(s) falharam.")


if __name__ == "__main__":
    main()
