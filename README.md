# Deep Atlas
Deep Atlas is a suite of tools created by the Blue Brain Project to manipulate
brain atlas images. 

## Full pipeline
See below a simplified sketch of the entire pipeline.
<img alt="Atlas Download Tools Banner" src="images/pipeline.svg" width="900"/>

Note that a lot of details are omitted and the user is encouraged to read
the `--help` of relevant scripts.

All the scripts are lying in the `pipeline/` directory.

```bash
pipeline/
├── download_gene.py
├── full_pipeline.py
├── gene_to_nissl.py
├── interpolate_gene.py
├── nissl_to_ccfv3.py
```

To run the entire pipeline one needs to use `full_pipeline.py`. However,
it is also possible to run different stages of the pipeline separately.

### `full_pipeline.py`

See below the `--help` of the `full_pipeline.py` script.

```bash
usage: full_pipeline.py [-h] --nissl-path NISSL_PATH --ccfv2-path CCFV2_PATH --experiment-id EXPERIMENT_ID --output-dir OUTPUT_DIR [--ccfv3-path CCFV3_PATH] [--coordinate-sys {ccfv2,ccfv3}] [--downsample-img DOWNSAMPLE_IMG]
                        [--interpolator-name {linear,rife,cain,maskflownet,raftnet}] [--interpolator-checkpoint INTERPOLATOR_CHECKPOINT] [-e] [-f]

optional arguments:
  -h, --help            show this help message and exit
  --nissl-path NISSL_PATH
                        Path to Nissl Volume. (default: None)
  --ccfv2-path CCFV2_PATH
                        Path to CCFv2 Volume. (default: None)
  --experiment-id EXPERIMENT_ID
                        Experiment ID from Allen Brain to use. (default: None)
  --output-dir OUTPUT_DIR
                        Path to directory where to save the results. (default: None)
  --ccfv3-path CCFV3_PATH
                        Path to CCFv3 Volume. (default: None)
  --coordinate-sys {ccfv2,ccfv3}
                        Downsampling coefficient for the image download. (default: ccfv2)
  --downsample-img DOWNSAMPLE_IMG
                        Downsampling coefficient for the image download. (default: 0)
  --interpolator-name {linear,rife,cain,maskflownet,raftnet}
                        Name of the interpolator model. (default: rife)
  --interpolator-checkpoint INTERPOLATOR_CHECKPOINT
                        Path of the interpolator checkpoints. (default: None)
  -e, --expression      If True, download and apply deformation to threshold images too. (default: False)
  -f, --force           If True, force to recompute every steps. (default: False)
```

The user is supposed to provide the following inputs (positional arguments)

* `nissl_path` - path to a Nissl volume
* `ccfv2_path` - path to an annotation volume in the CCFv2 reference space
* `ccfv3_path` - path to an annotation volume in the CCFv3 reference space
  (needed only if the `coordinate system` chosen is `CCFv3`)
* `experiment_id` - unique identifier of the ISH experiment
* `output_dir` - directory where to save the results


Note that there are multiple optional arguments. For example, one
can decide what coordinate system to use - `ccfv2` or `ccfv3`. By providing
the flag `--expression` preprocessed expression images are going to be
included. Finally, one can also pass stage specific parameters 
(e.g. `--interpolator-name` for the interpolation stage).

Concerning the interpolation part, machine learning models are used to make 
those predictions (except if the interpolator chosen is `linear`). It is then
needed to download the model and to specify to path through the 
`--interpolator-checkpoint` variable. To download the models, please follow the
instructions specified in the atlinter documentation 
[here](https://github.com/BlueBrain/atlas-interpolation#data).


## Docker
We provide a docker file that allows you to run the `pipeline` on a docker container. 
To build the docker image run the following command:

```bash
docker build -f docker/Dockerfile -t deep-atlas-pipeline .
```
To run the container use the following command:
```bash
docker run --rm -it deep-atlas-pipeline
```
### Specify user and group ids

By default, the user within the docker container is `guest`, its id is 1000, and its group is 999. \
Files created by this user within the container might not be accessible to the user running 
the container, if their ids do not match. \
If one wants to configure a specific user, one needs to adapt the `docker/Dockerfile` file, 
changing the following lines with the users .
```bash
ARG DEAL_USER_IDS
ARG DEAL_GROUP_ID=${DEAL_GROUP_ID:-999}
```
The list of users has a comma separated list of users with the format `<username>/<userid>`. \
Only one group id should be provided. The default user group is therefore recommended.

Alternatively, one can define the environment variable and add this info 
to the CLI command of `docker build`
```bash
export DEAL_USER_IDS="$(whoami)/$(id -u)"
export DEAL_GROUP_ID=$(id -g)
docker build -f docker/Dockerfile -t deep-atlas-pipeline \
--build-arg DEAL_USER_IDS --build-arg DEAL_GROUP_ID .
```

To specify the user to use when running the container, use the following command:
```bash
docker run --rm -it -u <username>  deep-atlas-pipeline
```

## Singularity for BB5
Docker is not supported in BB5 and [singularity](https://docs.sylabs.io/guides/3.5/user-guide/introduction.html) will be used instead.
1) ssh into BB5. 

`ssh bbpv1` or `ssh bbpv1.epfl.ch`.

2) Allocate an interactive session using Slurm. Note that you have to use a `projectID` that you have permissions for.
```bash
salloc \
--nodes 1 \
--account proj<X> \
--partition interactive \
--constraint volta \
--time 1:00:00 \
--ntasks-per-node 36
```
or with a shorter notation
```bash
salloc -N 1 -A proj<X> -p interactive -C volta -t 1:00:00 --ntasks-per-node 36
```
3) Load the singularity module.
```bash
module load unstable singularityce
```
4) Pull the docker image from GitLab.
```bash
singularity pull --docker-login --no-https docker://bbpgitlab.epfl.ch:5050/ml/deep-atlas:cuda10.2
```
A new file named `deep-atlas_cuda10.2.sif` will be created. This is your singularity image.

5) Run the singularity container:
```bash
singularity exec --cleanenv --nv --containall --bind $TMPDIR:/tmp,/gpfs/bbp.cscs.ch/project,$HOME:/home deep-atlas_cuda10.2.sif bash
```
There is no write access inside the singularity container. Results have to be written, for instance, to the `/home` directory that is linked to the `$HOME` of BB5 or to `GPFS` mounted at `/gpfs`. (see the option `--bind` above)

## Dependencies
The full pipeline depends on multiple other projects.
- [Atlas Download Tools](#atlas-download-tools) — Search, download, and prepare
  atlas data.
- [Atlas Alignment](#atlas-alignment) — Perform multimodal image registration
  and alignment.
- [Atlas Annotation](#atlas-annotation) — Image registration for region
  annotation atlases.
- [Atlas Interpolation](#atlas-interpolation) — Slice interpolation for atlases.

Each of the projects is described in more detail below.

### Atlas Download Tools
<img alt="Atlas Download Tools Banner" src="images/Atlas-Download-Tools-banner.jpg" width="600"/>

Useful links:
[GitHub repo](https://github.com/BlueBrain/Atlas-Download-Tools),
[Docs](https://atlas-download-tools.readthedocs.io).

**Search, download, and prepare atlas data.**

Among different sources of data, Allen Brain Institute hosts a rich database of
gene expression images, Nissl volumes, and annotation atlases. The
Atlas-Download-Tools library can help you to download single section images and
entire datasets, as well as the corresponding metadata. It can further
pre-process the image data to place it in the standard reference space.


### Atlas Alignment
<img alt="Atlas Alignment Banner" src="images/Atlas_Alignment_banner.jpg" width="600"/>

Useful links:
[GitHub repo](https://github.com/BlueBrain/atlas-alignment),
[Docs](https://atlas-alignment.readthedocs.io).

**Multimodal registration and alignment toolbox.**

Atlas Alignment is a toolbox to perform multimodal image registration. It
includes both traditional and supervised deep learning models. This project
originated from the Blue Brain Project efforts on aligning mouse brain atlases
obtained with ISH gene expression and Nissl stains.

### Atlas Annotation
<img alt="Atlas Annotation Banner" src="images/Atlas-Annotation-banner.jpg" width="600"/>

Useful links:
[GitHub repo](https://github.com/BlueBrain/atlas-annotation),
[Docs](https://atlas-annotation.readthedocs.io).

**Align and improve brain annotation atlases.**

Over the years the Allen Brain institute has constantly improved and updated
their brain region annotation atlases. Unfortunately the old annotation atlases
are not always aligned with the new ones. For example, the CCFv2 annotations
and the Nissl volume are not compatible with the CCFv3 annotation and the
corresponding average brain volume. This package proposes a number of methods
for deforming the Nissl volume and the CCFv2 annotations in order to re-align
them to CCFv3.

### Atlas Interpolation
<img alt="Atlas Interpolation Banner" src="images/Atlas-Interpolation.jpg" width="600"/>

Useful links:
[GitHub repo](https://github.com/BlueBrain/atlas-interpolation),
[Docs](https://atlas-interpolation.readthedocs.io).

**Interpolate missing section images in gene expression volumes.**

The Allen Brain Institute hosts a rich database of mouse brain imagery. It
contains a large number of gene expression datasets obtained
through the in situ hybridization (ISH) staining. While for a given gene
a number of datasets corresponding to different specimen can be found, each of
these datasets only contains sparse section images that do not form a
continuous volume. This package explores techniques that allow to interpolate
the missing slices and thus reconstruct whole gene expression volumes.


# Funding & Acknowledgment
The development of this software was supported by funding to the Blue Brain Project, a research center of the École polytechnique fédérale de Lausanne (EPFL), from the Swiss government's ETH Board of the Swiss Federal Institutes of Technology.
 
Copyright © 2021-2022 Blue Brain Project/EPFL


