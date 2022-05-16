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
        "--section-numbers",
        type=Path,
        help="""\
        Path to json containing section numbers of gene expression.
        """,
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        help="""\
        Path to save the resulting gene expression volume.
        """,
    )
    return parser.parse_args()


def main():
    """Main function."""
    import numpy as np

    from atlinter.data import GeneDataset
    from atlinter.pair_interpolation import GeneInterpolate, RIFEPairInterpolationModel
    from atlinter.vendor.rife.RIFE_HD import Model as RifeModel
    from atlinter.vendor.rife.RIFE_HD import device as rife_device

    args = parse_args()

    logger.info("Loading Data...")
    data_path = args.gene_path
    data_json = args.section_numbers

    section_images = np.load(data_path)
    with open(data_json) as fh:
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
    checkpoint_path = "data/checkpoints/rife"
    rife_model = RifeModel()
    rife_model.load_model(checkpoint_path, -1)
    rife_model.eval()
    rife_interpolation_model = RIFEPairInterpolationModel(rife_model, rife_device)

    # Create a gene interpolator
    gene_interpolate = GeneInterpolate(gene_dataset, rife_interpolation_model)

    # Reconstruct the whole volume. This might take some time.
    predicted_volume = gene_interpolate.predict_volume()

    if args.output_file:
        np.save(args.output_file, predicted_volume)
    else:
        gene_name = args.gene_path.stem
        np.save(f"interpolated_{gene_name}.npy", predicted_volume)

    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())