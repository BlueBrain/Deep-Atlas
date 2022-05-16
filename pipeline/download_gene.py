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
import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import PIL


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
        "--gene-name",
        type=str,
        help="""\
        Path to CCFv3 annotation volume.
        """,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="""\
        Path to output directory to save results.
        """,
    )
    args = parser.parse_args()

    return args


def postprocess_dataset(dataset):
    """Post process given dataset.

    Parameters
    ----------
    dataset : iterable
        List containing dataset, each element being tuple
        (img_id, section_coordinate, img, df)

    Returns
    -------
    dataset_np : np.ndarray
        Array containing gene expressions of the dataset.
    metadata_dict : dict
        Dictionary containing metadata of the dataset.
        Keys are section numbers and image ids.
    """
    metadata_dict = {}
    section_numbers = []
    image_ids = []
    dataset_np = []

    for img_id, section_coordinate, img, df in dataset:
        if section_coordinate is None:
            # In `atldld.sync.download_dataset` if there is a problem during the download
            # the generator returns `(img_id, None, None, None, None)
            # TODO: maybe notify the user somehow?
            continue

        section_numbers.append(section_coordinate // 25)
        image_ids.append(img_id)
        warped_img = df.warp(img, border_mode="constant", c=img[0, 0, :].tolist())
        dataset_np.append(warped_img)

    dataset_np = np.array(dataset_np)

    metadata_dict["section_numbers"] = section_numbers
    metadata_dict["image_ids"] = image_ids
    metadata_dict["image_shape"] = warped_img.shape

    return dataset_np, metadata_dict


def main(
    gene_name: str,
    output_dir: Path | str | None = None,
) -> int:
    """Download gene expression dataset."""
    # Imports
    import json

    from atldld.sync import download_dataset
    from atldld.utils import CommonQueries, get_experiment_list_from_gene

    # To avoid Decompression Warning
    PIL.Image.MAX_IMAGE_PIXELS = 200000000

    # Download dataset on allen
    if output_dir is None:
        output_dir = Path(__file__).parent / "download-gene" / gene_name
    else:
        output_dir = Path(output_dir) / gene_name

    if not output_dir.exists():
        output_dir.mkdir(parents=True)

    for axis in ['sagittal', 'coronal']:

        experiment_list = get_experiment_list_from_gene(gene_name, axis)
        for experiment_id in experiment_list:
            dataset = download_dataset(experiment_id)
            axis = CommonQueries.get_axis(experiment_id)
            dataset_np, metadata_dict = postprocess_dataset(dataset)
            metadata_dict["axis"] = axis

            np.save(output_dir / f"{experiment_id}.npy", dataset_np)
            with open(output_dir / f"{experiment_id}.json", 'w') as f:
                json.dump(metadata_dict, f)

    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    kwargs = vars(args)
    sys.exit(main(**kwargs))
