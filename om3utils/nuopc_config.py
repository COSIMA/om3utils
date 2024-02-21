"""NUOPC configuration"""

from pathlib import Path
import re


def _convert_from_string(value: str):
    """Tries to convert a string to the most appropriate type. Leaves the string unchanged if not conversion succeeds.

    :param value: value to convert.
    """
    # Start by trying to convert from a Fortran logical to a Python bool
    if value.lower() == ".true.":
        return True
    elif value.lower() == ".false.":
        return False
    # Next try to convert to integer or float
    for conversion in [
        lambda: int(value),
        lambda: float(value),
        lambda: float(value.replace("D", "e")),
    ]:
        try:
            out = conversion()
        except ValueError:
            continue
        return out
    # None of the above succeeded, so just return the string
    return value


def _convert_to_string(value) -> str:
    """Converts values to a string.

    :param value: value to convert.
    """
    if isinstance(value, bool):
        return ".true." if value else ".false."
    elif isinstance(value, float):
        return "{:e}".format(value).replace("e", "D")
    else:
        return str(value)


def read_nuopc_config(file_name: str) -> dict:
    """Read a NUOPC config file.

    :param file_name: File name.
    """
    fname = Path(file_name)
    if not fname.is_file():
        raise FileNotFoundError(f"File not found: {fname.as_posix()}")

    label_value_pattern = re.compile(r"\s*(\w+)\s*:\s*(.+)\s*")
    table_start_pattern = re.compile(r"\s*(\w+)\s*::\s*")
    table_end_pattern = re.compile(r"\s*::\s*")
    assignment_pattern = re.compile(r"\s*(\w+)\s*=\s*(\S+)\s*")

    config = {}
    with open(fname, "r") as stream:
        reading_table = False
        label = None
        table = None
        for line in stream:
            line = re.sub(r"(#).*", "", line)
            if line.strip():
                if reading_table:
                    if re.match(table_end_pattern, line):
                        config[label] = table
                        reading_table = False
                    else:
                        match = re.match(assignment_pattern, line)
                        if match:
                            table[match.group(1)] = _convert_from_string(match.group(2))
                        else:
                            raise ValueError(
                                f"Line: {line} in file {file_name} is not a valid NUOPC configuration specification"
                            )

                elif re.match(table_start_pattern, line):
                    reading_table = True
                    match = re.match(label_value_pattern, line)
                    label = match.group(1)
                    table = {}

                elif re.match(label_value_pattern, line):
                    match = re.match(label_value_pattern, line)
                    config[match.group(1)] = [_convert_from_string(string) for string in match.group(2).split()]

    return config


def write_nuopc_config(config: dict, file: Path):
    """Write a NUOPC config dictionary as a Resource File.

    :param config: Dictionary holding the NUOPC configuration to write
    :param file: File to write to.
    """
    with open(file, "w") as stream:
        for key, item in config.items():
            if isinstance(item, dict):
                stream.write(key + "::\n")
                for label, value in item.items():
                    stream.write("  " + label + " = " + _convert_to_string(value) + "\n")
                stream.write("::\n\n")
            else:
                stream.write(key + ": " + " ".join(map(_convert_to_string, item)) + "\n")
