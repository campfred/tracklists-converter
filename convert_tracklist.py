import argparse, yaml, pathlib, enum, typing

###
# Utilities declarations
class TracklistFormats(enum.Enum):
	Default = "Main"
	Telegram = "Telegram"
# type TrackInfo = dict[str, str]
TracklistHeaders: typing.Mapping[TracklistFormats, str] = {
	TracklistFormats.Telegram: "**TRACKLIST**"
}

def generate_track(data: typing.Mapping[str, str]) -> str:
	text = ""
	if "artist" in data:
		text += "{artist} - ".format(artist = data["artist"])
	text += data["title"]
	if "label" in data and not arguments.no_labels:
		text += " ({label})".format(label = data["label"])
	return text

def generate_timestamp(timestamp:str, data: typing.Mapping[str, str], format = TracklistFormats) -> str:
	if format == TracklistFormats.Telegram:
		return "{timestamp}  {track}".format(timestamp = timestamp, track = generate_track(data))
	else:
		return "[{timestamp}]  {track}".format(timestamp = timestamp, track = generate_track(data))



###
# Setting up
arguments_parser = argparse.ArgumentParser(
	prog = "Tracklist converter", 
	description = "Generates mixtape tracklist files for different formats based on a YAML chart.", 
	epilog = "The YAML files' content should be organized like the following : \"timestamp\": [title|artist|label]: text"
	)
arguments_parser.add_argument("-f", "--file", type = pathlib.Path, help = "Path of the input file to convert from.", default = "./Tracklist.yaml")
arguments_parser.add_argument("-o", "--output-dir", type = pathlib.Path, help = "Path of the output directory in which tracklists will be written.", default = ".")
arguments_parser.add_argument("-L", "--no-labels", action = "store_true", help = "Do not write label info.", default = False)
arguments = arguments_parser.parse_args()

##
# Checking files
# Input
# path_file_input = arguments.file if arguments.file else pathlib.Path("./Tracklist.yaml")
path_file_input = arguments.file
if not path_file_input.is_file():
	print("❗  Missing Tracklist file.\nℹ️ Maybe the script isn't being run in a directory where a « Tracklist.yaml » exists or the « file » argument has been forgotten.")
	exit(1)
print("➡️  Input tracklist file :\n\t" + str(path_file_input))
# Output
# path_output_directory = arguments.output_dir if arguments.output_dir else "."
path_output_directory = arguments.output_dir
print("⬅️  Output tracklist files :")
path_output_files: typing.Mapping[TracklistFormats, pathlib.Path] = {}
for tracklist_format in TracklistFormats:
	path_output_files[tracklist_format] = path_output_directory.joinpath("Tracklist.{format}.txt".format(format = tracklist_format.value))
	print("\t" + str(path_output_files[tracklist_format]))



###
# Going through files
print("📤  Loading origin tracklist...")
# https://stackoverflow.com/a/1774043
with open(file = path_file_input, mode = "r") as file_reader:
	try:
		tracklist = yaml.safe_load(file_reader)
		print("ℹ️ Tracklist loaded. {count} entries found.".format(count = len(tracklist)))
		file_reader.close()
	except yaml.YAMLError as exception:
		print(exception)
		exit(1)
print("📥  Writing destination tracklists...")
file_writers: dict = {}
with open(file = path_output_files[TracklistFormats.Default], mode="w") as file_writers[TracklistFormats.Default]:
	with open(path_output_files[TracklistFormats.Telegram], mode="w") as file_writers[TracklistFormats.Telegram]:
		# Writing headers
		print("\t🎩  Writing headers")
		for tracklist_format in TracklistFormats:
			if tracklist_format in TracklistHeaders:
				print("\t\t➡️  " + tracklist_format.name)
				file_writers[tracklist_format].write(TracklistHeaders[tracklist_format] + "\n")
		# Writing tracks
		print("\t📜  Writing track lists")
		for timestamp in tracklist:
			print("\t🎼 {title} at {timestamp}".format(title = tracklist[timestamp]["title"], timestamp = timestamp))
			for tracklist_format in TracklistFormats:
				file_writers[tracklist_format].write(generate_timestamp(timestamp, data = tracklist[timestamp], format = tracklist_format) + "\n")
				print("\t\t➡️  {format_name} format list".format(format_name = tracklist_format.name))
		print("✅  Tracklists written!")
		for tracklist_format in TracklistFormats:
			file_writers[tracklist_format].close()
