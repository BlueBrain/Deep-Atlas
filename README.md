# Deep Atlas
Deep Atlas is a suite of tools created by the Blue Brain Project to manipulate
brain atlas images. 
- [Atlas Download Tools](#atlas-download-tools) — Search, download, and prepare
  atlas data.
- [Atlas Alignment](#atlas-alignment) — Perform multimodal image registration
  and alignment.
- [Atlas Annotation](#atlas-annotation) — Image registration for region
  annotation atlases.
- [Atlas Interpolation](#atlas-interpolation) — Slice interpolation for atlases.

## Atlas Download Tools
<img alt="Atlas Download Tools Banner" src="images/Atlas-Download-Tools-banner.jpg" width="600"/>

Useful links:
[GitHub repo](https://github.com/BlueBrain/Atlas-Download-Tools),
[Docs](https://atlas-download-tools.readthedocs.io/en/latest).

**Search, download, and prepare atlas data.**

Among different sources of data, Allen Brain Institute hosts a rich database of
gene expression images, Nissl volumes, and annotation atlases. The
Atlas-Download-Tools library can help you to download single section images and
entire datasets, as well as the corresponding metadata. It can further
pre-process the image data to place it in the standard reference space.


## Atlas Alignment
<img alt="Atlas Alignment Banner" src="images/Atlas_Alignment_banner.jpg" width="600"/>

Useful links:
[GitHub repo](https://github.com/BlueBrain/atlas-alignment),
[Docs](https://atlas-alignment.readthedocs.io/en/latest).

**Multimodal registration and alignment toolbox.**

Atlas Alignment is a toolbox to perform multimodal image registration. It
includes both traditional and supervised deep learning models. This project
originated from the Blue Brain Project efforts on aligning mouse brain atlases
obtained with ISH gene expression and Nissl stains.

## Atlas Annotation
Useful links:
[GitHub repo](https://github.com/BlueBrain/atlas-annotation).

**Align and improve brain annotation atlases.**

Over the years the Allen Brain institute has constantly improved and updated
their brain region annotation atlases. Unfortunately the old annotation atlases
are not always aligned with the new ones. For example, the CCFv2 annotations
and the Nissl volume are not compatible with the CCFv3 annotation and the
corresponding average brain volume. This package proposes a number of methods
for deforming the Nissl volume and the CCFv2 annotations in order to re-align
them to CCFv3.

## Atlas Interpolation
Useful links:
[GitHub repo](https://github.com/BlueBrain/atlas-interpolation).

**Interpolate missing section images in gene expression volumes.**

The Allen Brain Institute hosts a rich database of mouse brain imagery. It
contains a large number of gene expression datasets obtained
through the in situ hybridization (ISH) staining. While for a given gene
a number of datasets corresponding to different specimen can be found, each of
these datasets only contains sparse section images that do not form a
continuous volume. This package explores techniques that allow to interpolate
the missing slices and thus reconstruct whole gene expression volumes.
