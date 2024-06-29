# Tracklist converter

This project is the home of a simple tracklist convert.

It originates from the need to generate multiple track list formats at once since I use YAML to write down my tracklists in an organized manner.

## Options

| Name         | Short | Description                                                       | Required | Default                 |
| ------------ | ----- | ----------------------------------------------------------------- | -------- | ----------------------- |
| `file`       | `f`   | Path of the input file to convert from.                           | ✖️        | `./Tracklist.yaml`      |
| `output-dir` | `o`   | Path of the output directory in which tracklists will be written. | ✖️        | `.` (Current directory) |
| `no-labels`  | `L`   | Do not write label info.                                          | ✖️        | `False`                 |

## How to run

Call the script from the current directory and enjoy!
Ex.: `python convert_tracklist.py`, `python convert_tracklist.py --input List.yml --output-dir Tracklists --no-labels`
