#! /usr/bin/python3

"""
Simple script to recursively convert AIFF and WAV files to 44.1kHz 16bit mono PCM.
Ideal for use with Polyend Play.
Only files that are not already in the right format will be converted.
Requires Python 3.
Usage: ./polyend-play-convert.py ~/Samples
"""

import os
import re
import sys
import subprocess
from pathlib import Path
from dataclasses import dataclass

from mutagen import File
from pydub import AudioSegment

AUDIO_EXTENSION = ".wav"
AUDIO_CHANNELS = 1
AUDIO_SAMPLE_RATE = 44100
AUDIO_BIT_DEPTH = 705600
AUDIO_FORMAT_TYPE = "audio/wav"

@dataclass
class FileToConvert:
    path: Path
    audio_channels: int
    sample_rate: int
    bit_depth: int
    format_type: str


def get_files_recursive(
    target_path: Path,
) -> list[Path]:
    """
    Recursively gets audio files anywhere in `path`.
    """
    waves = target_path.rglob(f"**/*.wav")
    aiffs = target_path.rglob(f"**/*.aiff")
    aifs = target_path.rglob(f"**/*.aif")
    return [
        child for child in list(waves) + list(aiffs) + list(aifs) if child.is_file()
    ]


def get_namespace_from_tag(tag: str) -> str:
    m = re.match(r"{.*}", tag)
    return m.group(0) if m else ""


def convert():
    try:
        # Run `ffmpeg -version` to check if ffmpeg is installed
        result = subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            raise FileNotFoundError()
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise SystemExit(f"FFmpeg is not installed or not found in the system PATH.")
    
    try:
        target_folder = sys.argv[1]
        if not target_folder:
            raise ValueError()
    except (IndexError, ValueError):
        raise SystemExit(f"Usage: {sys.argv[0]} <target_folder>")

    target_path = Path(target_folder)
    if not target_path.is_dir():
        raise SystemExit(f"Not a valid directory: {sys.argv[1]}")

    # Loop all the files and get only those that need to be converted
    file_paths = get_files_recursive(target_path)
    files_to_convert: list[FileToConvert] = []
    for file_path in file_paths:
        audio = File(file_path)
        
        audio_channels = audio.info.channels if hasattr(audio.info, 'channels') else "Unknown"
        sample_rate = audio.info.sample_rate if hasattr(audio.info, 'sample_rate') else "Unknown"
        bit_depth = audio.info.bitrate if hasattr(audio.info, 'bitrate') else "Unknown"
        format_type = audio.mime[0] if audio.mime else "Unknown"
        
        if (
            file_path.suffix != AUDIO_EXTENSION
            or audio_channels != AUDIO_CHANNELS
            or sample_rate != AUDIO_SAMPLE_RATE
            or bit_depth != AUDIO_BIT_DEPTH
            or format_type != AUDIO_FORMAT_TYPE
        ):
            files_to_convert.append(
                FileToConvert(
                    path=file_path,
                    audio_channels=audio_channels,
                    sample_rate=sample_rate,
                    bit_depth=bit_depth,
                    format_type=format_type,
                )
            )

    if not files_to_convert:
        raise SystemExit(f"No WAV/AIFF files found that need conversion.")

    # Confirm
    proceed = input(
        f"Are you sure that you want to convert all {len(files_to_convert)} files "
        f"in the following directory to 44.1kHz 16bit mono PCM WAV?"
        f"\n\n{target_path}\n\ny/N\n\n"
    )
    if proceed.lower() not in ["y", "yes"]:
        raise SystemExit("Cancelled.")

    # Convert
    for file_to_convert in files_to_convert:
        audio_file_path = str(file_to_convert.path)
        
        audio = AudioSegment.from_file(audio_file_path)
        # Convert to mono
        audio = audio.set_channels(1)
        
        # Set frame rate to 44.1kHz
        audio = audio.set_frame_rate(44100)
        
        # Export as 16-bit PCM WAV file (705 kbps)
        output_file_path = file_to_convert.path.with_suffix(AUDIO_EXTENSION)
        audio.export(output_file_path, format="wav", parameters=["-acodec", "pcm_s16le"])
        
        if file_to_convert.path.suffix != AUDIO_EXTENSION:
            os.unlink(file_to_convert.path)
        print(f"- {str(file_to_convert.path).replace(target_folder, '')}")

    print("\n\nAll done.\n\n")

if __name__ == "__main__":
    convert()