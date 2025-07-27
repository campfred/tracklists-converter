import argparse, yaml, pathlib, enum, typing, csv, mimetypes
from datetime import datetime


###
# Setting up
arguments_parser = argparse.ArgumentParser(
    prog="Tracklist converter",
    description="Generates mixtape tracklist files for different formats based on a YAML or CSV chart.",
    epilog='The YAML files should be organized as "timestamp": [title|artist|label]: text. CSV files should have columns: timestamp,title,artist,label',
)
arguments_parser.add_argument(
    "-i",
    "--input",
    type=pathlib.Path,
    help="Path of the input file to convert from.",
    default="./Tracklist.yaml",
)
arguments_parser.add_argument(
    "-o",
    "--output-dir",
    type=pathlib.Path,
    help="Path of the output directory in which tracklists will be written.",
    default=".",
)
arguments_parser.add_argument(
    "-L",
    "--no-labels",
    action="store_true",
    help="Do not write music label info.",
    default=False,
)
cue_group = arguments_parser.add_argument_group("cue sheet options")
cue_group.add_argument(
    "--audio-file",
    type=str,
    help="Path to the audio file (required for CUE sheet generation)",
    default=None,
)
cue_group.add_argument(
    "--audio-type",
    type=str,
    choices=["MP3", "WAVE", "AIFF"],
    help="Type of the audio file for CUE sheet. If not specified, it will be detected automatically.",
    default=None,
)
cue_group.add_argument(
    "--mix-title",
    type=str,
    help="Title of the mix for CUE sheet",
    default="DJ Mix",
)
cue_group.add_argument(
    "--mix-performer",
    type=str,
    help="Performer name for CUE sheet",
    default="Various Artists",
)

format_group = arguments_parser.add_argument_group("output formats")
format_group.add_argument(
    "--format",
    type=str,
    choices=["Main", "Telegram", "Lyrics", "CUE"],
    help="The format type(s) to export (Main, Telegram, Lyrics, or CUE). Can be specified multiple times.",
    action="append",
    default=[],
)
format_group.add_argument(
    "--main",
    action="store_true",
    help="Export in Main format",
    default=False,
)
format_group.add_argument(
    "--telegram",
    action="store_true",
    help="Export in Telegram format",
    default=False,
)
format_group.add_argument(
    "--lyrics",
    action="store_true",
    help="Export in Lyrics format",
    default=False,
)
format_group.add_argument(
    "--cue",
    action="store_true",
    help="Export in CUE sheet format",
    default=False,
)
arguments = arguments_parser.parse_args()

# Combine format flags with format argument
selected_formats = arguments.format
if arguments.main:
    selected_formats.append("Main")
if arguments.telegram:
    selected_formats.append("Telegram")
if arguments.lyrics:
    selected_formats.append("Lyrics")
if arguments.cue:
    if not arguments.audio_file:
        print("❗ Error: --audio-file is required when generating CUE sheet format")
        exit(1)
    selected_formats.append("CUE")

# If no format was specified, default to Main
if not selected_formats:
    selected_formats = ["Main"]


class InputFormats(enum.Enum):
    YAML = "yaml"
    CSV = "csv"


###
# Utilities declarations
class TracklistFormats(enum.Enum):
    Default = "Main"
    Telegram = "Telegram"
    Lyrics = "Lyrics"
    CUE = "CUE"


def detect_audio_type(file_path: str) -> str:
    """Detect the type of audio file and return the appropriate CUE format type."""
    if not file_path:
        return "MP3"  # Default if no file specified
    
    path = pathlib.Path(file_path)
    if not path.exists():
        print(f"⚠️  Warning: Audio file {file_path} not found. Using extension to guess type.")
    
    # Initialize mimetypes
    mimetypes.init()
    
    # Get the mime type based on file extension
    mime_type, _ = mimetypes.guess_type(file_path)
    
    if mime_type:
        if "audio/mpeg" in mime_type or "audio/mp3" in mime_type:
            return "MP3"
        elif "audio/wav" in mime_type or "audio/x-wav" in mime_type:
            return "WAVE"
        elif "audio/aiff" in mime_type or "audio/x-aiff" in mime_type:
            return "AIFF"
    
    # Fallback to extension check if mime type is not conclusive
    suffix = path.suffix.lower()
    if suffix in [".mp3", ".mp2"]:
        return "MP3"
    elif suffix in [".wav", ".wave"]:
        return "WAVE"
    elif suffix in [".aiff", ".aif"]:
        return "AIFF"
    
    print(f"⚠️  Warning: Could not determine audio type for {file_path}. Defaulting to MP3.")
    return "MP3"


# type TrackInfo = dict[str, str]
TracklistHeaders: typing.Mapping[TracklistFormats, str] = {
    TracklistFormats.Telegram: "**TRACKLIST**",
    TracklistFormats.CUE: 'PERFORMER "{performer}"\nTITLE "{title}"\nFILE "{file}" {type}'
}


def generate_track(data: typing.Mapping[str, str]) -> str:
    text = ""
    if "artist" in data:
        text += "{artist} - ".format(artist=data["artist"])
    text += data["title"]
    if "label" in data and data["label"] and not arguments.no_labels:
        text += " ({label})".format(label=data["label"])
    return text


def timestamp_to_frames(timestamp: str) -> str:
    """Convert MM:SS to MM:SS:FF format (75 frames per second)"""
    parts = timestamp.split(":")
    if len(parts) == 2:
        minutes, seconds = map(int, parts)
        return f"{minutes:02d}:{seconds:02d}:00"
    return "00:00:00"

def generate_timestamp(
    timestamp: str, data: typing.Mapping[str, str], format=TracklistFormats
) -> str:
    if format == TracklistFormats.Telegram:
        return "{timestamp} {track}".format(
            timestamp=timestamp, track=generate_track(data)
        )
    elif format == TracklistFormats.Lyrics:
        # Convert MM:SS to [MM:SS.00] format required for lyrics
        return "[{timestamp}.00]{track}".format(
            timestamp=timestamp, track=generate_track(data)
        )
    elif format == TracklistFormats.CUE:
        track_num = data.get("track_num", 1)
        frames_timestamp = timestamp_to_frames(timestamp)
        return (
            f'  TRACK {track_num:02d} AUDIO\n'
            f'    TITLE "{data["title"]}"\n'
            f'    PERFORMER "{data["artist"]}"\n'
            f'    INDEX 01 {frames_timestamp}'
        )
    else:
        return "[{timestamp}] {track}".format(
            timestamp=timestamp, track=generate_track(data)
        )


def parse_input_file(file_path: pathlib.Path) -> dict:
    input_format = (
        InputFormats.YAML if file_path.suffix.lower() == ".yaml" else InputFormats.CSV
    )

    with open(file=file_path, mode="r") as file_reader:
        if input_format == InputFormats.YAML:
            try:
                return yaml.safe_load(file_reader)
            except yaml.YAMLError as exception:
                print(exception)
                exit(1)
        else:
            tracklist = {}
            csv_reader = csv.DictReader(file_reader)
            for row in csv_reader:
                timestamp = row["timestamp"]
                tracklist[timestamp] = {
                    "title": row["title"],
                    "artist": row["artist"],
                    "label": row["label"],
                }
            return tracklist


def sort_tracklist(tracklist: dict) -> dict:
    def timestamp_to_seconds(timestamp: str) -> int:
        parts = timestamp.split(":")
        if len(parts) == 2:
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        return 0

    return dict(sorted(tracklist.items(), key=lambda x: timestamp_to_seconds(x[0])))

##
# Checking files
# Input
# path_file_input = arguments.file if arguments.file else pathlib.Path("./Tracklist.yaml")
path_file_input = arguments.file
if not path_file_input.is_file():
    print(
        "❗  Missing Tracklist file.\nℹ️ Maybe the script isn't being run in a directory where a « Tracklist.yaml » exists or the « file » argument has been forgotten."
    )
    exit(1)
print("➡️  Input tracklist file :\n\t" + str(path_file_input))

# Output
path_output_directory = arguments.output_dir
print("⬅️  Output tracklist files:")
format_enums = [TracklistFormats[format_type] for format_type in selected_formats]
output_files = {
    format_type: path_output_directory.joinpath(
        "Tracklist.{format}.txt".format(format=format_type.value)
    )
    for format_type in format_enums
}
for output_file in output_files.values():
    print("\t" + str(output_file))

###
# Going through files
print("📤  Loading origin tracklist...")
tracklist = parse_input_file(path_file_input)
tracklist = sort_tracklist(tracklist)
print("ℹ️ Tracklist loaded. {count} entries found.".format(count=len(tracklist)))

print("📥  Writing destination tracklists...")
for current_format, output_file in output_files.items():
    print(f"\n📝 Generating {current_format.value} format...")
    with open(file=output_file, mode="w") as file_writer:
        # Writing header if it exists for the format
        if current_format in TracklistHeaders:
            print("\t🎩  Writing header")
            if current_format == TracklistFormats.CUE:
                audio_type = arguments.audio_type or detect_audio_type(arguments.audio_file)
                header = TracklistHeaders[current_format].format(
                    performer=arguments.mix_performer,
                    title=arguments.mix_title,
                    file=arguments.audio_file,
                    type=audio_type
                )
            else:
                header = TracklistHeaders[current_format]
            file_writer.write(header + "\n")
        
        # Writing tracks
        print("\t📜  Writing track list")
        for track_num, (timestamp, track_data) in enumerate(tracklist.items(), 1):
            print(
                "\t🎼 {title} at {timestamp}".format(
                    title=track_data["title"], timestamp=timestamp
                )
            )
            # Add track number for CUE format
            if current_format == TracklistFormats.CUE:
                track_data = track_data.copy()  # Create a copy to avoid modifying original
                track_data["track_num"] = track_num
            
            file_writer.write(
                generate_timestamp(
                    timestamp, data=track_data, format=current_format
                )
                + "\n"
            )
        print("\t✅  Format written!")
print("\n✨ All tracklists written successfully!")

def detect_audio_type(file_path: str) -> str:
    """Detect the type of audio file and return the appropriate CUE format type."""
    if not file_path:
        return "MP3"  # Default if no file specified
    
    path = pathlib.Path(file_path)
    if not path.exists():
        print(f"⚠️  Warning: Audio file {file_path} not found. Using extension to guess type.")
    
    # Initialize mimetypes
    mimetypes.init()
    
    # Get the mime type based on file extension
    mime_type, _ = mimetypes.guess_type(file_path)
    
    if mime_type:
        if "audio/mpeg" in mime_type or "audio/mp3" in mime_type:
            return "MP3"
        elif "audio/wav" in mime_type or "audio/x-wav" in mime_type:
            return "WAVE"
        elif "audio/aiff" in mime_type or "audio/x-aiff" in mime_type:
            return "AIFF"
    
    # Fallback to extension check if mime type is not conclusive
    suffix = path.suffix.lower()
    if suffix in [".mp3", ".mp2"]:
        return "MP3"
    elif suffix in [".wav", ".wave"]:
        return "WAVE"
    elif suffix in [".aiff", ".aif"]:
        return "AIFF"
    
    print(f"⚠️  Warning: Could not determine audio type for {file_path}. Defaulting to MP3.")
    return "MP3"
