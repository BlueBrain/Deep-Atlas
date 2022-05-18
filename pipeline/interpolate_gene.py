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
"""Script that interpolates Gene Expression."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path


logger = logging.getLogger("interpolate-gene")


def parse_args():
    """Parse arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--gene-path",
        type=Path,
        help="""\
        Path to Gene Expression.
        """,
    )
    parser.add_argument(
        "--metadata-path",
        type=Path,
        help="""\
        Path to json containing metadata of gene expression.
        """,
    )
    parser.add_argument(
        "--interpolator-name",
        type=str,
        choices=("linear", "rife", "cain", "maskflownet", "raftnet"),
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
        Path to directory where to save the resulting gene expression volume.
        """,
    )
    return parser.parse_args()


def load_interpolator_model(interpolator_name: str, checkpoint: str | Path):

    checkpoint = Path(checkpoint)
    if not checkpoint.exists():
        raise ValueError(f"The checkpoint path {checkpoint} does not exist.")

    if interpolator_name == "rife":
        from atlinter.pair_interpolation import RIFEPairInterpolationModel
        from atlinter.vendor.rife.RIFE_HD import Model as RifeModel
        from atlinter.vendor.rife.RIFE_HD import device as rife_device

        rife_model = RifeModel()
        rife_model.load_model(checkpoint, -1)
        rife_model.eval()
        model = RIFEPairInterpolationModel(rife_model, rife_device)

    elif interpolator_name == "cain":
        import torch

        from atlinter.vendor.cain.cain import CAIN
        from atlinter.pair_interpolation import CAINPairInterpolationModel

        device = "cuda" if torch.cuda.is_available else "cpu"
        cain_model = torch.nn.DataParallel(CAIN()).to(device)
        cain_checkpoint = torch.load(checkpoint, map_location=device)
        cain_model.load_state_dict(cain_checkpoint["state_dict"])
        model = CAINPairInterpolationModel(cain_model)

    elif interpolator_name == "linear":
        from atlinter.pair_interpolation import LinearPairInterpolationModel

        model = LinearPairInterpolationModel()

    elif interpolator_name == "maskflownet":
        from atlinter.optical_flow import MaskFlowNet

        model = MaskFlowNet(checkpoint)

    elif interpolator_name == "raftnet":
        from atlinter.optical_flow import RAFTNet

        model = RAFTNet(checkpoint)

    else:
        raise ValueError(
            f"The interpolator model {interpolator_name} is not supported yet."
            f"Choices are: 'rife', 'cain', 'maskflownet', 'raftnet', 'linear'"
        )

    return model


def main(
    gene_path: Path | str,
    metadata_path: Path | str,
    interpolator_name: str,
    interpolator_checkpoint: str | Path,
    reference_path: str | Path,
    output_dir: Path | str | None = None,
) -> int:
    """Implement main function."""
    import numpy as np

    from atlinter.data import GeneDataset

    logger.info("Loading Data...")
    section_images = np.load(gene_path)
    with open(metadata_path) as fh:
        metadata = json.load(fh)

    section_numbers = [int(s) for s in metadata["section_numbers"]]
    axis = metadata["axis"]

    # Wrap the data into a GeneDataset class
    gene_dataset = GeneDataset(
        section_images,
        section_numbers,
        volume_shape=(528, 320, 456, 3),
        axis=axis,
    )

    logger.info("Loading interpolator model...")
    interpolator_model = load_interpolator_model(
        interpolator_name, interpolator_checkpoint
    )

    # Create a gene interpolator
    logger.info("Start interpolating the entire volume...")
    if interpolator_name in {"cain", "rife"}:
        from atlinter.pair_interpolation import GeneInterpolate

        gene_interpolate = GeneInterpolate(gene_dataset, interpolator_model)
        predicted_volume = gene_interpolate.predict_volume()
    else:
        from atlinter.optical_flow import GeneOpticalFlow

        reference_volume = np.load(reference_path)
        gene_optical_flow = GeneOpticalFlow(
            gene_dataset, reference_volume, interpolator_model
        )
        predicted_volume = gene_optical_flow.predict_volume()

    gene_name = Path(gene_path).stem.split("-")[0]

    if output_dir is None:
        output_dir = Path(__file__).parent / "interpolate-gene"
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    np.save(
        output_dir / f"{gene_name}-{interpolator_name}-interpolated-gene.npy",
        predicted_volume,
    )

    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    kwargs = vars(args)
    sys.exit(main(**kwargs))