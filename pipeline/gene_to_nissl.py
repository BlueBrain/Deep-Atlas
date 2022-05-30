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
"""Script that maps Gene Expression to Nissl."""
from __future__ import annotations

import argparse
import json
import logging
import pathlib
import sys
from pathlib import Path

import nrrd
import numpy as np
from skimage.color import rgb2gray

from atlannot.ants import register, transform

# Initialize the logger
logger = logging.getLogger("gene-to-nissl")


def parse_args():
    """Parse arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "gene_path",
        type=Path,
        help="""\
        Path to Gene Expression.
        """,
    )
    parser.add_argument(
        "metadata_path",
        type=Path,
        help="""\
        Path to json containing metadata of gene expression.
        """,
    )
    parser.add_argument(
        "nissl_path",
        type=Path,
        help="""\
        Path to Nissl Volume.
        """,
    )
    parser.add_argument(
        "output_dir",
        type=Path,
        help="""\
        Path to directory where to save the results.
        """,
    )
    parser.add_argument(
        "--expression-path",
        type=Path,
        help="""\
        If specified, transformation also applied to the given numpy.
        """,
    )
    return parser.parse_args()


def registration(
    nissl_volume: np.ndarray,
    gene_volume: np.ndarray,
    section_numbers: np.ndarray,
    expression_volume: np.ndarray | None,
) -> tuple[np.ndarray, np.ndarray | None, list[bool]]:
    """Compute registration transform between a couple of volumes.

    Parameters
    ----------
    nissl_volume
        Nissl volume (fixed volume during registration).
    gene_volume
        Gene to register (moving volume during registration).
    section_numbers
        Section numbers of every gene slice in gene volume.
    expression_volume
        If specified, volume to which we apply same transform
        as the gene_volume.

    Returns
    -------
    warped_genes : np.ndarray
        Warped slice.
    warped_expression : np.ndarray | None
        Warped expression.
    section_numbers_kept : list[bool]
        Boolean value saying if section was kept or removed.
    """
    rgb = False
    if gene_volume.ndim == 4:
        rgb = True

    warped_genes = []
    warped_expression = []
    section_numbers_kept = []
    for i, (section_number, gene_slice) in enumerate(zip(section_numbers, gene_volume)):
        try:
            nissl_slice = nissl_volume[int(section_number)]
        except IndexError:
            logger.warn(
                f"One of the gene slice has a section number ({section_number})"
                f"out of nissl volume shape {nissl_volume.shape}. This slice is"
                "removed from the pipeline."
            )
            section_numbers_kept.append(False)
            continue

        if rgb:
            gene_slice_rgb = gene_slice.copy()
            gene_slice = rgb2gray(gene_slice)

        nii_data = register(nissl_slice, gene_slice, is_atlas=False)

        if rgb:
            warped = np.zeros_like(gene_slice_rgb)
            warped[:, :, 0] = transform(gene_slice_rgb[:, :, 0], nii_data)
            warped[:, :, 1] = transform(gene_slice_rgb[:, :, 1], nii_data)
            warped[:, :, 2] = transform(gene_slice_rgb[:, :, 2], nii_data)
        else:
            warped = transform(gene_slice, nii_data)

        warped_genes.append(warped)

        if expression_volume is not None:
            expression = expression_volume[i]
            warped = np.zeros_like(expression)
            warped[:, :, 0] = transform(expression[:, :, 0], nii_data)
            warped[:, :, 1] = transform(expression[:, :, 1], nii_data)
            warped[:, :, 2] = transform(expression[:, :, 2], nii_data)

            warped_expression.append(warped)

        section_numbers_kept.append(True)

        if (i + 1) % 5 == 0:
            logger.info(f" {i + 1} / {gene_volume.shape[0]} registrations done")

    warped_expression = np.array(warped_expression) if warped_expression else None

    return np.array(warped_genes), warped_expression, section_numbers_kept


def main(
    gene_path: Path | str,
    metadata_path: Path | str,
    nissl_path: Path | str,
    output_dir: Path | str,
    expression_path: str | Path | None = None,
) -> int:
    """Implement main function."""
    from utils import check_and_load

    gene_path = Path(gene_path)
    metadata_path = Path(metadata_path)
    nissl_path = Path(nissl_path)
    output_dir = Path(output_dir)
    if expression_path is not None:
        expression_path = Path(expression_path)

    logger.info("Loading volumes")
    nissl = check_and_load(nissl_path)
    genes = check_and_load(gene_path)
    experiment_id = gene_path.stem

    expression = None
    if expression_path is not None:
        expression = check_and_load(expression_path)

    with open(metadata_path) as f:
        json_dict = json.load(f)

    section_numbers = json_dict["section_numbers"]
    axis = json_dict["axis"]

    if axis == "sagittal":
        nissl = np.transpose(nissl, (2, 0, 1))

    if nissl.shape[1:] != genes.shape[1:3]:
        raise ValueError(
            f"It seems the nissl ({nissl.shape}) and genes ({genes.shape}) "
            "do not have the same shape !"
        )

    if genes.shape[0] != len(section_numbers):
        raise ValueError(
            f"The length of the list of the section numbers ({len(section_numbers)})"
            f" has to be consistent to the genes shape ({genes.shape[0]})"
        )

    logger.info("Start registration...")

    warped_genes, warped_expression, section_numbers_kept = registration(
        nissl, genes, section_numbers, expression_volume=expression
    )

    logger.info("Saving results...")
    output_dir.mkdir(parents=True, exist_ok=True)
    np.save(output_dir / f"{experiment_id}-warped-gene", warped_genes)

    json_dict["section_numbers"] = [
        image_id
        for image_id, kept in zip(json_dict["section_numbers"], section_numbers_kept)
        if kept
    ]
    json_dict["image_ids"] = [
        image_id
        for image_id, kept in zip(json_dict["image_ids"], section_numbers_kept)
        if kept
    ]

    with open(output_dir / f"{experiment_id}-metadata.json", "w") as f:
        json.dump(json_dict, f)

    if warped_expression is not None:
        np.save(output_dir / f"{experiment_id}-warped-expression", warped_expression)

    return 0


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    args = parse_args()
    kwargs = vars(args)
    sys.exit(main(**kwargs))
