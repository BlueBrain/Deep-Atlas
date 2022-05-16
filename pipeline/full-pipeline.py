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
        "--nissl-path",
        type=Path,
        help="""\
        Path to Nissl Volume.
        """,
    )
    parser.add_argument(
        "--ccfv2-path",
        type=Path,
        help="""\
        Path to CCFv2 Volume.
        """,
    )
    parser.add_argument(
        "--ccfv3-path",
        type=Path,
        help="""\
        Path to CCFv3 Volume.
        """,
    )
    parser.add_argument(
        "--gene-name",
        type=Path,
        help="""\
        Gene Expression to use.
        """,
    )
    parser.add_argument(
        "--interpolator-name",
        type=str,
        choices=("rife", "cain", "maskflownet", "raftnet"),
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
        "--reference-path",
        type=Path,
        help="""\
        Path to the reference volume used for the optical flow prediction.
        If interpolation model is "cain" or "rife", there is no need to 
        specify a reference path.
        """,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="""\
        Path to directory where to save the results.
        """,
    )
    return parser.parse_args()


def main(
    nissl_path: Path | str,
    ccfv2_path: Path | str,
    ccfv3_path: Path | str,
    gene_name: str,
    interpolator_name: str,
    interpolator_checkpoint: Path | str,
    output_dir: Path | str | None,
    reference_path: str | None = None,
) -> int:
    """Implement the main function."""
    from download_gene import main as download_gene_main
    from gene_to_nissl import main as gene_to_nissl_main
    from interpolate_gene import main as interpolate_gene_main
    from nissl_to_ccfv3 import main as nissl_to_ccfv3_main

    if output_dir is None:
        output_dir = Path(__file__).parent / "full-pipeline"
    else:
        output_dir = Path(output_dir)

    warped_nissl_path = output_dir / "nissl-to-ccfv3" / "warped_nissl.npy"
    if not warped_nissl_path.exists():
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
            f"Nissl is already aligned and saved {warped_nissl_path}"
        )

    logger.info("Downloading Gene Expression...")
    download_gene_main(gene_name, output_dir=output_dir / "download-gene")

    gene_experiment_path = output_dir / "download-gene" / gene_name
    experiments_results = {filename.stem for filename in gene_experiment_path.iterdir()}

    logger.info("Aligning downloaded Gene Expression to new Nissl volume...")
    for experiment in experiments_results:
        logger.info(f"Aligning Gene Expression Experiment {experiment} to new Nissl volume...")
        gene_to_nissl_main(
            gene_path=gene_experiment_path / f"{experiment}.npy",
            metadata_path=gene_experiment_path / f"{experiment}.json",
            nissl_path=warped_nissl_path,
            output_dir=output_dir / "gene-to-nissl" / gene_name,
        )

    aligned_gene_path = output_dir / "gene-to-nissl" / gene_name
    experiments_results = {filename.stem for filename in aligned_gene_path.iterdir()}
    logger.info("Interpolating the missing slices of the gene expression...")
    for experiment in experiments_results:
        interpolate_gene_main(
            gene_path=aligned_gene_path / f"{experiment}.npy",
            metadata_path=aligned_gene_path / f"{experiment}.json",
            interpolator_name=interpolator_name,
            interpolator_checkpoint=interpolator_checkpoint,
            reference_path=reference_path,
            output_dir=output_dir / "interpolate-gene" / gene_name,
        )

    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    kwargs = vars(args)
    sys.exit(main(**kwargs))
