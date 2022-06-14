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
"""Utility functions for the full pipeline."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from atlannot.utils import load_volume


def check_and_load(path: Path | str, normalize: bool = False) -> np.ndarray:
    """Load volume if path exists.

    Parameters
    ----------
    path
        File path.
    normalize
        If True, output volume values are between 0 and 1.
        Otherwise, volume is kept raw.

    Returns
    -------
    volume : np.ndarray
        Loaded volume.

    Raises
    ------
    ValueError
        When the path specified does not exist.
    """
    path = Path(path)
    if not path.exists():
        raise ValueError(f"The specified path {path} does not exist.")

    volume = load_volume(path, normalize=normalize)
    return volume
