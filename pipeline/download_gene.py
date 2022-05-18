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
"""Script that download and postprocess ISH dataset from Allen Brain."""
from __future__ import annotations

import argparse
import logging
import sys
from tqdm import tqdm
from pathlib import Path
from typing import Any, Generator, Optional, Tuple

import numpy as np
import PIL
from atldld.base import DisplacementField


logger = logging.getLogger("download-gene")


def parse_args():
    """Parse command line arguments.

    Returns
    -------
    args : argparse.Namespace
        The parsed command line arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "gene_name",
        type=str,
        help="""\
        Name of the gene to download.
        """,
    )
    parser.add_argument(
        "output_dir",
        type=Path,
        help="""\
        Path to output directory to save results.
        """,
    )
    parser.add_argument(
        "--downsample-img",
        type=int,
        default=0,
        help="""\
        Factor of downsampling of the images when downloading them.
        """,
    )
    args = parser.parse_args()

    return args


def postprocess_dataset(
    dataset: Generator[
        Tuple[int, float, np.ndarray, Optional[np.ndarray], DisplacementField],
        None,
        None,
    ],
    n_images: int,
) -> Tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Post process given dataset.

    Parameters
    ----------
    dataset
        List containing dataset, each element being tuple
        (img_id, section_coordinate, img, img_expression, df)
    n_images
        The overall number of slices we are going to download.
        Needs to be passed separately since the `dataset` is a generator.

    Returns
    -------
    dataset_np : np.ndarray
        Array containing gene expressions of the dataset.
    expression_np : np.ndarray
        Array containing image expression of the dataset.
    metadata_dict : dict
        Dictionary containing metadata of the dataset.
        Keys are section numbers and image ids.
    """
    metadata_dict = {}
    section_numbers = []
    image_ids = []
    expression_np = []
    dataset_np = []

    for img_id, section_coordinate, img, img_expression, df in tqdm(
        dataset, total=n_images
    ):
        if section_coordinate is None:
            # In `atldld.sync.download_dataset` if there is a problem during the download
            # the generator returns `(img_id, None, None, None, None)
            # TODO: maybe notify the user somehow?
            continue

        section_numbers.append(section_coordinate // 25)
        image_ids.append(img_id)
        warped_img = 255 - df.warp(img, border_mode="constant", c=img[0, 0, :].tolist())
        warped_exp = df.warp(
            img_expression, border_mode="constant", c=img[255, 255, :].tolist()
        )
        dataset_np.append(warped_img)
        expression_np.append(warped_exp)

    dataset_np = np.array(dataset_np)
    expression_np = np.array(expression_np)

    metadata_dict["section_numbers"] = section_numbers
    metadata_dict["image_ids"] = image_ids
    metadata_dict["image_shape"] = warped_img.shape

    return dataset_np, expression_np, metadata_dict


def main(
    gene_name: str,
    output_dir: Path | str,
    downsample_img: int,
) -> int:
    """Download gene expression dataset.

    Parameters
    ----------
    gene_name
        Gene name to download.
    output_dir
        Directory when results are going to be saved.
    downsample_img
        Downsampling factor given to Allen API when downloading the images.
        This factor is going to reduce the size.
    """
    # Imports
    import json

    from atldld.sync import DatasetDownloader
    from atldld.utils import CommonQueries, get_experiment_list_from_gene

    # To avoid Decompression Warning
    PIL.Image.MAX_IMAGE_PIXELS = 200000000

    # Download dataset on allen
    output_dir = Path(output_dir) / gene_name

    if not output_dir.exists():
        output_dir.mkdir(parents=True)

    for axis in ["sagittal", "coronal"]:

        experiment_list = get_experiment_list_from_gene(gene_name, axis)
        logger.info(f"{gene_name} have {len(experiment_list)} for {axis} axis")
        for experiment_id in experiment_list:
            logger.info(f"Start downloading experiment ID {experiment_id}")
            dataset = DatasetDownloader(
                experiment_id, downsample_img=downsample_img, include_expression=True
            )
            dataset.fetch_metadata()
            dataset_gen = dataset.run()
            axis = CommonQueries.get_axis(experiment_id)
            dataset_np, expression_np, metadata_dict = postprocess_dataset(
                dataset_gen, len(dataset))
            metadata_dict["axis"] = axis

            logger.info(f"Saving results of experiment ID {experiment_id}")
            np.save(output_dir / f"{experiment_id}-expression.npy", expression_np)
            np.save(output_dir / f"{experiment_id}.npy", dataset_np)
            with open(output_dir / f"{experiment_id}.json", "w") as f:
                json.dump(metadata_dict, f, indent=True, sort_keys=True)

    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    kwargs = vars(args)
    sys.exit(main(**kwargs))
