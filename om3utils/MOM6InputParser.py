import re


class MOM6InputParser(object):
    header_pattern = re.compile(r"^! === (.+) ===")
    block_list = [
        "KPP%",
        "%KPP",
        "CVMix_CONVECTION%",
        "%CVMix_CONVECTION",
        "CVMIX_DDIFF%",
        "%CVMIX_DDIFF",
    ]

    def __init__(self):
        self.param_dict = {}
        self.commt_dict = {}
        self.current_var = None
        self.current_value = []
        self.current_comment = []
        self.block_pattern = re.compile(r"|".join(re.escape(i) for i in self.block_list))

    def read_input(self, MOM_input_read_path):
        with open(MOM_input_read_path, "r") as f:
            self.lines = f.readlines()

    def parse_lines(self):
        for line in self.lines:
            if self.header_pattern.match(line):
                self._save_current_param()
                self._start_new_header()
                continue

            if line.strip().startswith("!"):
                self._append_comments(line)
                continue

            if "=" in line:
                self._save_current_param()
                self._parse_params(line)

            elif self.block_pattern.search(line):  # block_pattern
                self._save_current_param()
                self._parse_params_block(line)

        # last parameter
        self._save_current_param()

    def _save_current_param(self):
        # save parameters, and associated values and comments
        if self.current_var:
            var_name = self.current_var
            value = "".join(self.current_value).strip()
            comment = "\n".join(self.current_comment).strip()
            self.param_dict[var_name] = value
            self.commt_dict[var_name] = comment

    def _start_new_header(self):
        self.current_var = None
        self.current_value = []
        self.current_comment = []

    def _parse_params(self, line):
        param, value = line.split("=", 1)
        param = param.strip()
        # separate value and inline comment
        tmp_value = value.split("!")[0].strip()  # value
        tmp_commt = value.split("!")[1].strip() if "!" in value else ""  # inline comment
        self.current_var = param
        self.current_value = [tmp_value]
        self.current_comment = [tmp_commt]

    def _parse_params_block(self, line):
        self.current_var = line.strip()
        self.current_value = [""]
        self.current_comment = [""]

    def _append_comments(self, line):
        if self.current_var:
            self.current_comment.append(line.strip())

    def writefile_MOM_input(self, MOM_input_write_path, total_width=32):
        """
        Write the updated MOM_input to file
        """
        with open(MOM_input_write_path, "w") as f:
            f.write("! This file was written by the script xxx \n")
            f.write("! and records the non-default parameters used at run-time.\n")
            f.write("\n")
            for var, value in self.param_dict.items():
                comment = self.commt_dict.get(var, "")
                if comment:
                    comment_lines = comment.split("\n")
                    param_str = f"{var} = {value}"
                    f.write(f"{param_str:<{total_width}} ! {comment_lines[0].strip()}\n")
                    for comment_line in comment_lines[1:]:
                        f.write(f"{'':<{total_width}} {comment_line.strip()}\n")
                elif var in self.block_list:
                    f.write(f"{var}\n")
                else:
                    f.write(f"{var} = {value}\n")
            f.write("\n")
