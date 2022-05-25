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
"""Script that run the full pipeline."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

logger = logging.getLogger("full-pipeline")


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
        Path to CCFv2 Volume.
        """,
    )
    parser.add_argument(
        "ccfv3_path",
        type=Path,
        help="""\
        Path to CCFv3 Volume.
        """,
    )
    parser.add_argument(
        "experiment_id",
        type=int,
        help="""\
        Experiment ID from Allen Brain to use.
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
        "--coordinate-sys",
        type=str,
        default="ccfv2",
        choices=("ccfv2", "ccfv3"),
        help="""\
        Downsampling coefficient for the image download.
        """,
    )
    parser.add_argument(
        "--downsample-img",
        type=int,
        default=0,
        help="""\
        Downsampling coefficient for the image download.
        """,
    )
    parser.add_argument(
        "--interpolator-name",
        type=str,
        choices=("linear", "rife", "cain", "maskflownet", "raftnet"),
        default="rife",
        help="""\
        Name of the interpolator model.
        """,
    )
    parser.add_argument(
        "--interpolator-checkpoint",
        type=str,
        help="""\
        Path of the interpolator checkpoints.
        """,
    )
    parser.add_argument(
        "-e",
        "--expression",
        action="store_true",
        help="""\
        If True, download and apply deformation to threshold images too.
        """,
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="""\
        If True, force to recompute every steps.
        """,
    )
    return parser.parse_args()


def main(
    nissl_path: Path | str,
    ccfv2_path: Path | str,
    ccfv3_path: Path | str,
    experiment_id: int,
    coordinate_sys: str,
    downsample_img: int,
    interpolator_name: str,
    interpolator_checkpoint: Path | str | None,
    output_dir: Path | str,
    expression: bool = False,
    force: bool = False,
) -> int:
    """Implement the main function."""
    from download_gene import main as download_gene_main
    from gene_to_nissl import main as gene_to_nissl_main
    from interpolate_gene import main as interpolate_gene_main
    from nissl_to_ccfv3 import main as nissl_to_ccfv3_main

    output_dir = Path(output_dir)

    if coordinate_sys == "ccfv3":
        warped_nissl_path = output_dir / "nissl-to-ccfv3" / "warped-nissl.npy"
        if not warped_nissl_path.exists() or force:
            logger.info("Aligning Nissl volume to CCFv3 annotation volume...")
            nissl_to_ccfv3_main(
                nissl_path,
                ccfv2_path,
                ccfv3_path,
                output_dir=output_dir / "nissl-to-ccfv3",
            )
        else:
            logger.info(
                "Aligning Nissl volume to CCFv3 annotation volume: Skipped \n"
                f"Nissl is already aligned and saved under {warped_nissl_path}"
            )

        nissl_path = warped_nissl_path

    gene_experiment_dir = output_dir / "download-gene"
    gene_experiment_path = gene_experiment_dir / f"{experiment_id}.npy"
    if not gene_experiment_path.exists() or force:
        logger.info("Downloading Gene Expression...")
        download_gene_main(
            experiment_id,
            output_dir=gene_experiment_dir,
            downsample_img=downsample_img,
            expression=expression,
        )
    else:
        logger.info(
            "Downloading Gene Expression: Skipped \n"
            f"{gene_id} is already downloaded and saved under {gene_experiment_path}"
        )

    aligned_results_dir = output_dir / "gene-to-nissl" / coordinate_sys
    aligned_gene_path = aligned_results_dir / f"{experiment_id}-warped-gene.npy"

    if not aligned_gene_path.exists() or force:
        logger.info(f"Aligning downloaded Gene Expression to Nissl volume in {coordinate_sys} ({nissl_path})...")
        gene_to_nissl_main(
            gene_path=gene_experiment_dir / f"{experiment_id}.npy",
            metadata_path=gene_experiment_dir / f"{experiment_id}.json",
            nissl_path=nissl_path,
            output_dir=aligned_results_dir,
            expression_path=gene_experiment_dir / f"{experiment_id}-expression.npy"
            if expression
            else None,
        )
    else:
        logger.info("Aligning downloaded Gene Expression to Nissl volume: Skipped")

    interpolation_results_dir = output_dir / "interpolate-gene" / coordinate_sys
    interpolated_gene_path = (
        interpolation_results_dir
        / f"{experiment_id}-{interpolator_name}-interpolated-gene.npy"
    )

    if not interpolated_gene_path.exists() or force:
        logger.info("Interpolating the missing slices of the gene expression...")
        paths = [
            aligned_results_dir / f"{experiment_id}-warped-gene.npy",
        ]
        if expression:
            paths += [
                aligned_results_dir / f"{experiment_id}-warped-expression.npy",
            ]

        for path in paths:
            interpolate_gene_main(
                gene_path=path,
                metadata_path=aligned_results_dir / f"{experiment_id}-metadata.json",
                interpolator_name=interpolator_name,
                interpolator_checkpoint=interpolator_checkpoint,
                reference_path=nissl_path,
                output_dir=interpolation_results_dir,
            )

    return 0


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    args = parse_args()
    kwargs = vars(args)
    sys.exit(main(**kwargs))
