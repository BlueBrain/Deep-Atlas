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
"""Script that maps Nissl to CCFv3."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
from atlannot.ants import register, transform

logger = logging.getLogger("nissl-to-ccfv3")


def parse_args():
    """Parse arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "nissl_path",
        type=Path,
        help="""\
        Path to Nissl Volume.
        """,
    )
    parser.add_argument(
        "ccfv2_path",
        type=Path,
        help="""\
        Path to CCFv2 annotation volume.
        """,
    )
    parser.add_argument(
        "ccfv3_path",
        type=Path,
        help="""\
        Path to CCFv3 annotation volume.
        """,
    )
    parser.add_argument(
        "output_dir",
        type=Path,
        help="""\
        Path to output directory to save results.
        """,
    )
    return parser.parse_args()


def registration(
    reference_volume: np.ndarray, moving_volume: np.ndarray, nissl_volume: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Compute registration between a moving volume and reference one.

    Parameters
    ----------
    reference_volume
        Reference volume of annotation type.
    moving_volume
        Moving volume (annotation) of the same shape as the moving_volume.
    nissl_volume
        Nissl volume to register. It has to have same shape as reference_volume
        and moving_volume and be from the same coordinate system as the moving
        volume.

    Returns
    -------
    warped_volume : np.ndarray
        Moving volume after the registration transformation.
    nissl_warped : np.ndarray
        Nissl volume once the registration transformation are applied.
    """
    logger.info("Compute the registration...")
    nii_data = register(reference_volume, moving_volume)
    logger.info(f"Max displacements: {np.abs(nii_data).max(axis=(0, 1, 2, 3))}")

    logger.info("Apply transformation to Moving Volume...")
    warped_volume = transform(moving_volume, nii_data, interpolator="genericLabel")

    logger.info("Apply transformation to Nissl Volume...")
    nissl_warped = transform(nissl_volume, nii_data)

    return warped_volume, nissl_warped


def main(
    nissl_path: Path | str,
    ccfv2_path: Path | str,
    ccfv3_path: Path | str,
    output_dir: Path | str,
) -> int:
    """Implement main function."""
    from atlannot.utils import Remapper
    from utils import check_and_load

    logger.info("Loading volumes")
    nissl = check_and_load(nissl_path)
    ccfv2 = check_and_load(ccfv2_path)
    ccfv3 = check_and_load(ccfv3_path)

    logger.info("Remapping CCFv2 and CCFv3 volumes to consecutive labels")
    remapper = Remapper(ccfv2, ccfv3)
    ccfv2 = remapper.remap_old_to_new(0)
    ccfv3 = remapper.remap_old_to_new(1)

    logger.info("Start registration...")
    warped_atlas, warped_nissl = registration(ccfv3, ccfv2, nissl)

    logger.info("Remapping CCFv2 to original labels")
    warped_atlas = remapper.remap_new_to_old(warped_atlas)

    logger.info("Saving results...")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    np.save(output_dir / "warped-ccfv2", warped_atlas)
    np.save(output_dir / "warped-nissl", warped_nissl)

    return 0


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    args = parse_args()
    kwargs = vars(args)
    sys.exit(main(**kwargs))
