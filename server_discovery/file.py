import os
import json
import sys

reload(sys)
sys.setdefaultencoding("utf-8")


class File(object):

    """This class writes and reads files."""

    def __init__(self, file_name):
        self.file_name = file_name

    def append(self, string):
        """Append string to self.file_name."""

        with open(self.file_name, 'a') as file:
            file.write(string)

    def append_lines(self, lines):
        """Append list of lines to self.file_name."""

        self.append('\n'.join(lines))

    def read(self):
        """Read self.file_name."""

        with open(self.file_name, 'r') as file:
            return file.read().strip()

    def read_lines(self):
        """Read self.file_name and return list of lines."""
        if os.path.isfile(self.file_name):
            return [line.strip() for line in self.read().splitlines()]
        else:
            return []

    def read_json(self):
        """Read JSON and return."""
        if os.path.isfile(self.file_name):
            return json.load(open(self.file_name))
        else:
            return None

    def write(self, string):
        """Write string to self.file_name."""

        with open(self.file_name, 'w') as file:
            file.write(string)

    def write_lines(self, lines):
        """Write list of lines to self.file_name."""

        self.write('\n'.join(lines))

    def write_json(self, data):
        """Write JSON to self.file_name."""

        json.dump(data, open(self.file_name, 'w'), ensure_ascii = False)
