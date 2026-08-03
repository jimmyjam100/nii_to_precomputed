# nii_to_precomputed
Utilities for converting .nii/.nii.gz volumes into Neuroglancer precomputed image or segmentation layers, with optional mesh generation (via [igneous](https://github.com/seung-lab/igneous)), and serving them locally with HTTP requests.

Structure and conventions follow [lincbrain/trk_to_annotation](https://github.com/lincbrain/trk_to_annotation).

## Install
```
python -m build
pip install .
```

## Usage
```
python -m nii_to_precomputed <nii_file> \
    --output_dir ./precomputed_volume \
    --layer_type auto \
    --mesh
```

Layer type is auto-detected (integer dtype + a "dseg"/"seg"/"label" filename hint, or a low unique-value ratio, becomes a segmentation; everything else becomes an image), or can be forced with `--layer_type {segmentation,image}`.

For segmentation layers, a same-basename FreeSurfer-style LUT (`<id> <name> <r> <g> <b> <a>` per line, e.g. BIDS `..._dseg.txt` next to `..._dseg.nii.gz`) is picked up automatically and written out as a `segment_properties` sidecar (label names in Neuroglancer's segment list) plus a `segment_colors.json` snippet (paste into a layer's `"segmentColors"` to restore the LUT's colors — Neuroglancer's segment_properties format has no native color type).

Arguments
| Argument | Required | Default | Description |
| :---:   | :---: | :---: | :---: |
| nii_file | ✅ | — | Path to the input .nii/.nii.gz file |
| --output_dir | ❌ | ./precomputed_volume | Output directory for the precomputed layer |
| --layer_type | ❌ | auto | `auto`, `segmentation`, or `image` |
| --lut | ❌ | auto-detected | Path to a FreeSurfer-style LUT |
| --chunk_size | ❌ | 64 64 64 | Precomputed chunk size (voxels) |
| --encoding | ❌ | raw | CloudVolume encoding |
| --mesh | ❌ | off | Build meshes via igneous (segmentation only) |
| --mesh_mip | ❌ | 0 | Mip level to mesh |
| --mesh_shape | ❌ | 448 448 448 | Meshing task chunk shape (voxels) |
| --dust_threshold | ❌ | none | Skip meshing objects below this voxel count |
| --parallel | ❌ | 1 | Local worker processes for meshing |
| --skip_segment_properties | ❌ | off | Don't write segment_properties/segment_colors.json |
| --background_id | ❌ | 0 | Label id excluded from segment_properties/colors |

## Running server for neuroglancer

Run the following command in the directory with your outputted folder
```
python -m nii_to_precomputed.http_server
```

You should now be able to access the layer on neuroglancer via http://localhost:8000/
