#!/usr/bin/env python3
"""
Build script para renderizar videos de Manim.

Uso:
    python build.py                    # Renderizar todos los videos
    python build.py --list             # Listar escenas disponibles
    python build.py --video intro      # Renderizar video específico
    python build.py --quality high     # Renderizar en calidad alta
    python build.py --open             # Abrir video después de renderizar
    python build.py --combine          # Combinar todos en un solo video
"""

import argparse
import platform
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Configuración
VIDEOS_DIR = Path("videos")
MEDIA_DIR = Path("media")
QUALITY_FLAGS = {
    "low": "-ql",      # 480p15
    "medium": "-qm",   # 720p30
    "high": "-qh",     # 1080p60
    "4k": "-qk",       # 2160p60
}

# Mapeo de calidad a subdirectorio de output
QUALITY_DIRS = {
    "low": "480p15",
    "medium": "720p30",
    "high": "1080p60",
    "4k": "2160p60",
}


def open_video(file_path: Path) -> bool:
    """Abre un video con el reproductor predeterminado del sistema."""
    if not file_path.exists():
        print(f"   ⚠ Archivo no encontrado: {file_path}")
        return False

    system = platform.system()
    try:
        if system == "Darwin":  # macOS
            subprocess.run(["open", str(file_path)], check=True)
        elif system == "Windows":
            subprocess.run(["start", str(file_path)], shell=True, check=True)
        elif system == "Linux":
            subprocess.run(["xdg-open", str(file_path)], check=True)
        else:
            print(f"   ⚠ Sistema no soportado para abrir: {system}")
            return False
        print(f"   🎥 Abierto: {file_path.name}")
        return True
    except subprocess.CalledProcessError:
        print(f"   ⚠ No se pudo abrir: {file_path}")
        return False
    except FileNotFoundError:
        print(f"   ⚠ Comando no encontrado para abrir archivos en {system}")
        return False


def discover_scenes() -> dict[str, list[dict]]:
    """Descubre todas las escenas en videos/."""
    scenes_by_folder = {}

    for folder in sorted(VIDEOS_DIR.iterdir()):
        if not folder.is_dir():
            continue

        scene_files = list(folder.glob("*.py"))
        if not scene_files:
            continue

        folder_scenes = []
        for scene_file in scene_files:
            # Extraer clases Scene del archivo
            scene_classes = extract_scene_classes(scene_file)
            for cls_name in scene_classes:
                folder_scenes.append({
                    "file": scene_file,
                    "class": cls_name,
                    "folder": folder.name,
                    "path": str(scene_file),
                })

        if folder_scenes:
            scenes_by_folder[folder.name] = folder_scenes

    return scenes_by_folder


def extract_scene_classes(file_path: Path) -> list[str]:
    """Extrae nombres de clases Scene de un archivo Python."""
    classes = []
    try:
        content = file_path.read_text()
        # Buscar clases que hereden de Scene o sus subclases
        import re
        pattern = r'class\s+(\w+)\s*\([^)]*Scene[^)]*\)\s*:'
        matches = re.findall(pattern, content)
        classes.extend(matches)
    except Exception as e:
        print(f"  ⚠ Error leyendo {file_path}: {e}")
    return classes


def list_scenes(scenes: dict[str, list[dict]]) -> None:
    """Muestra las escenas disponibles."""
    print("\n📁 Escenas disponibles:\n")

    for folder, folder_scenes in scenes.items():
        print(f"  📂 {folder}/")
        for scene in folder_scenes:
            print(f"     └── {scene['class']} ({scene['file'].name})")
        print()

    total = sum(len(s) for s in scenes.values())
    print(f"  Total: {total} escenas en {len(scenes)} carpetas\n")


def find_scene_by_name(scenes: dict[str, list[dict]], name: str) -> Optional[dict]:
    """Busca una escena por nombre (parcial, case-insensitive)."""
    name_lower = name.lower()

    for folder_scenes in scenes.values():
        for scene in folder_scenes:
            if name_lower in scene["class"].lower():
                return scene
            if name_lower in scene["folder"].lower():
                return scene

    return None


def render_scene(scene: dict, quality: str = "low", preview: bool = False, open_after: bool = False) -> bool:
    """Renderiza una escena individual."""
    quality_flag = QUALITY_FLAGS.get(quality, "-ql")
    cmd = ["manim", quality_flag, scene["path"], scene["class"]]

    if preview:
        cmd.insert(1, "-p")  # Abrir preview de manim durante render

    print(f"\n🎬 Renderizando: {scene['class']} ({quality})")
    print(f"   Archivo: {scene['path']}")
    print(f"   Comando: {' '.join(cmd)}\n")

    try:
        subprocess.run(cmd, check=True, capture_output=False)
        print(f"   ✅ Completado: {scene['class']}")

        # Abrir video con reproductor del sistema si se solicitó
        if open_after:
            quality_dir = QUALITY_DIRS.get(quality, "480p15")
            video_path = MEDIA_DIR / "videos" / scene["file"].stem / quality_dir / f"{scene['class']}.mp4"
            open_video(video_path)

        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error renderizando {scene['class']}: {e}")
        return False
    except FileNotFoundError:
        print("   ❌ Error: manim no encontrado. ¿Activaste el venv?")
        return False


def combine_videos(scenes: dict[str, list[dict]], quality: str = "low", open_after: bool = False) -> bool:
    """Combina múltiples escenas en un solo video usando ffmpeg."""
    # Primero renderizar todas las escenas
    print("\n📼 Renderizando escenas para combinar...\n")

    rendered_files = []
    for folder_scenes in scenes.values():
        for scene in folder_scenes:
            if render_scene(scene, quality):
                # Construir path del archivo renderizado
                quality_dir = QUALITY_DIRS.get(quality, "480p15")
                output_path = (
                    MEDIA_DIR / "videos" / scene["file"].stem /
                    quality_dir / f"{scene['class']}.mp4"
                )
                if output_path.exists():
                    rendered_files.append(output_path)

    if not rendered_files:
        print("❌ No hay videos para combinar")
        return False

    # Crear lista de archivos para ffmpeg
    list_file = MEDIA_DIR / "concat_list.txt"
    with open(list_file, "w") as f:
        for video in rendered_files:
            f.write(f"file '{video.absolute()}'\n")

    # Archivo de salida combinado
    output_file = MEDIA_DIR / "combined_output.mp4"

    print(f"\n📼 Combinando {len(rendered_files)} videos...")
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        str(output_file),
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ Video combinado: {output_file}")
        # Limpiar archivo temporal
        list_file.unlink()

        # Abrir video combinado si se solicitó
        if open_after:
            open_video(output_file)

        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error combinando videos: {e}")
        return False
    except FileNotFoundError:
        print("❌ Error: ffmpeg no encontrado. Instala con: brew install ffmpeg")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Build script para videos de Manim",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python build.py --list                    Listar escenas
  python build.py                          Renderizar todas
  python build.py --video intro            Renderizar 'intro'
  python build.py --video intro -o         Renderizar y abrir
  python build.py --video IntroScene -q h  Renderizar en alta calidad
  python build.py --combine                Combinar todas en un video
  python build.py --combine -o             Combinar y abrir resultado
        """,
    )

    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="Listar escenas disponibles",
    )
    parser.add_argument(
        "--video", "-v",
        type=str,
        help="Renderizar video específico (nombre parcial)",
    )
    parser.add_argument(
        "--quality", "-q",
        choices=["low", "medium", "high", "4k"],
        default="low",
        help="Calidad de renderizado (default: low)",
    )
    parser.add_argument(
        "--preview", "-p",
        action="store_true",
        help="Abrir preview de manim durante el render",
    )
    parser.add_argument(
        "--combine", "-c",
        action="store_true",
        help="Combinar todas las escenas en un solo video",
    )
    parser.add_argument(
        "--open", "-o",
        action="store_true",
        help="Abrir video con el reproductor del sistema después de renderizar",
    )

    args = parser.parse_args()

    # Verificar que estamos en el directorio correcto
    if not VIDEOS_DIR.exists():
        print("❌ Error: Directorio 'videos/' no encontrado")
        print("   Ejecuta este script desde la raíz del proyecto")
        sys.exit(1)

    # Descubrir escenas
    scenes = discover_scenes()

    if not scenes:
        print("❌ No se encontraron escenas en videos/")
        sys.exit(1)

    # Modo: listar
    if args.list:
        list_scenes(scenes)
        return

    # Modo: combinar
    if args.combine:
        success = combine_videos(scenes, args.quality, args.open)
        sys.exit(0 if success else 1)

    # Modo: renderizar específico
    if args.video:
        scene = find_scene_by_name(scenes, args.video)
        if not scene:
            print(f"❌ No se encontró escena que coincida con '{args.video}'")
            print("   Usa --list para ver las escenas disponibles")
            sys.exit(1)

        success = render_scene(scene, args.quality, args.preview, args.open)
        sys.exit(0 if success else 1)

    # Modo: renderizar todos
    print(f"\n🎬 Renderizando todas las escenas (calidad: {args.quality})\n")

    success_count = 0
    fail_count = 0

    for folder, folder_scenes in scenes.items():
        print(f"\n📂 {folder}/")
        for scene in folder_scenes:
            if render_scene(scene, args.quality, args.preview, args.open):
                success_count += 1
            else:
                fail_count += 1

    print(f"\n{'='*50}")
    print(f"✅ Exitosos: {success_count}")
    print(f"❌ Fallidos: {fail_count}")
    print(f"{'='*50}\n")

    sys.exit(0 if fail_count == 0 else 1)


if __name__ == "__main__":
    main()
