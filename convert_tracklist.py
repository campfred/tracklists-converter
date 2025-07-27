import argparse, yaml, pathlib, enum, typing, csv
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
format_group = arguments_parser.add_argument_group("output formats")
format_group.add_argument(
    "--format",
    type=str,
    choices=["Main", "Telegram", "Lyrics"],
    help="The format type(s) to export (Main, Telegram, or Lyrics). Can be specified multiple times.",
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
arguments = arguments_parser.parse_args()

# Combine format flags with format argument
selected_formats = arguments.format
if arguments.main:
    selected_formats.append("Main")
if arguments.telegram:
    selected_formats.append("Telegram")
if arguments.lyrics:
    selected_formats.append("Lyrics")

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


# type TrackInfo = dict[str, str]
TracklistHeaders: typing.Mapping[TracklistFormats, str] = {
    TracklistFormats.Telegram: "**TRACKLIST**"
}


def generate_track(data: typing.Mapping[str, str]) -> str:
    text = ""
    if "artist" in data:
        text += "{artist} - ".format(artist=data["artist"])
    text += data["title"]
    if "label" in data and data["label"] and not arguments.no_labels:
        text += " ({label})".format(label=data["label"])
    return text


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
            file_writer.write(TracklistHeaders[current_format] + "\n")
        
        # Writing tracks
        print("\t📜  Writing track list")
        for timestamp in tracklist:
            print(
                "\t🎼 {title} at {timestamp}".format(
                    title=tracklist[timestamp]["title"], timestamp=timestamp
                )
            )
            file_writer.write(
                generate_timestamp(
                    timestamp, data=tracklist[timestamp], format=current_format
                )
                + "\n"
            )
        print("\t✅  Format written!")
print("\n✨ All tracklists written successfully!")
