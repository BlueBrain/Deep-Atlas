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
from pathlib import Path

import nrrd
import numpy as np


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
    return parser.parse_args()


def main(input_path: Path, output_path: Path) -> int:

    array = np.load(input_path)
    nrrd.write(str(output_path), array)
    return 0


if __name__ == "__main__":
    main(**vars(parse_args()))
