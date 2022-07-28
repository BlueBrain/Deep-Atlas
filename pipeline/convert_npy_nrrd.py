#!/usr/bin/env python
# Copyright 2021, Blue Brain Project, EPFL
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
from collections import OrderedDict
from pathlib import Path

import nrrd
import numpy as np

# Match voxcell requirements:
HEADER = OrderedDict(
    [
        ("type", "uint32"),
        ("dimension", 3),
        ("space dimension", 3),
        ("sizes", None),
        (
            "space directions",
            np.array([[25.0, 0.0, 0.0], [0.0, 25.0, 0.0], [0.0, 0.0, 25.0]]),
        ),
        ("endian", "little"),
        ("encoding", "gzip"),
        ("space origin", np.array([0.0, 0.0, 0.0])),
    ]
)


def parse_args():
    """Parse command line arguments.

    Returns
    -------
    args : argparse.Namespace
        The parsed command line arguments.
    """
    """Parse arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input_path",
        type=Path,
        help="""\
        Path to the input volume.
        """,
    )
    parser.add_argument(
        "output_path",
        type=Path,
        help="""\
        Path to the output volume.
        """,
    )
    parser.add_argument(
        "-h",
        "--header",
        type=Path,
        help=f"""\
        If specified, the header {HEADER} is saved.
        """,
    )
    return parser.parse_args()


def main(input_path: Path, output_path: Path, header: bool) -> int:

    array = np.load(input_path)
    if header:
        HEADER["sizes"] = np.array(array.shape)
        nrrd.write(str(output_path), array, header=HEADER)
    else:
        nrrd.write(str(output_path), array)
    return 0


if __name__ == "__main__":
    main(**vars(parse_args()))
