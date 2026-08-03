"""
Main entry point for converting a .nii/.nii.gz volume into a Neuroglancer
precomputed image or segmentation layer, optionally with meshes.

Author: Matthieu Chourrout
License: Apache-2.0
"""

import argparse
import logging
import time

import numpy as np

from nii_to_precomputed.preprocessing import load_nifti, detect_layer_type
from nii_to_precomputed.layer import make_cloudvolume, write_volume
from nii_to_precomputed.segment_properties import write_segment_properties
from nii_to_precomputed.utils import load_lut, find_sibling_lut

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def main(
    nii_file: str,
    output_dir: str,
    layer_type: str = "auto",
    lut_path: str = None,
    chunk_size: list = [64, 64, 64],
    encoding: str = None,
    with_mesh: bool = False,
    mesh_mip: int = 0,
    mesh_shape: list = [448, 448, 448],
    dust_threshold: int = None,
    parallel: int = 1,
    skip_segment_properties: bool = False,
    background_id: int = 0,
):
    """
    Parameters
    ----------
    nii_file : str
        Path to the input .nii/.nii.gz file.
    output_dir : str
        Destination directory (or "gs://"/"s3://" URL) for the
        precomputed layer.
    layer_type : str
        "auto", "segmentation", or "image".
    lut_path : str, optional
        Path to a FreeSurfer-style LUT. If omitted, a same-basename .txt
        next to nii_file is used if present.
    chunk_size : list[int]
        Precomputed chunk size (x, y, z), in voxels.
    encoding : str, optional
        CloudVolume encoding. Defaults to "raw" for both layer types if
        not given.
    with_mesh : bool
        Build meshes via igneous (segmentation layers only).
    mesh_mip, mesh_shape, dust_threshold, parallel
        Passed through to meshing.build_meshes.
    skip_segment_properties : bool
        Skip writing segment_properties/segment_colors.json even if a LUT
        is found.
    background_id : int
        Label id treated as background and excluded from
        segment_properties/segment_colors (default 0).
    """
    start_time = time.time()

    data, affine, voxel_sizes_mm = load_nifti(nii_file)
    if data.ndim > 3:
        data = data[..., 0]

    resolved_type = detect_layer_type(nii_file, data) if layer_type == "auto" else layer_type
    logging.info("Layer type: %s", resolved_type)

    resolved_encoding = encoding or "raw"

    lut = None
    present_ids = None
    if resolved_type == "segmentation":
        present_ids = np.unique(data)
        present_ids = present_ids[present_ids != background_id]
        resolved_lut_path = find_sibling_lut(nii_file, lut_path)
        if resolved_lut_path and not skip_segment_properties:
            logging.info("Using LUT: %s", resolved_lut_path)
            lut = load_lut(resolved_lut_path)

    vol = make_cloudvolume(
        output_dir,
        data,
        voxel_sizes_mm,
        resolved_type,
        chunk_size=chunk_size,
        encoding=resolved_encoding,
        with_mesh=with_mesh,
        with_segment_properties=(lut is not None),
    )
    write_volume(vol, data)

    if resolved_type == "segmentation" and lut is not None:
        write_segment_properties(output_dir, lut, present_ids)

    if resolved_type == "segmentation" and with_mesh:
        from nii_to_precomputed.meshing import build_meshes
        build_meshes(
            output_dir,
            mip=mesh_mip,
            shape=mesh_shape,
            dust_threshold=dust_threshold,
            parallel=parallel,
        )

    logging.info("Done in %.2f seconds.", time.time() - start_time)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert a .nii/.nii.gz volume into a Neuroglancer precomputed layer"
    )
    parser.add_argument("nii_file", type=str, help="Path to the input .nii/.nii.gz file")
    parser.add_argument(
        "--output_dir", type=str, default="./precomputed_volume",
        help="Output directory for the precomputed layer",
    )
    parser.add_argument(
        "--layer_type", type=str, default="auto",
        choices=["auto", "segmentation", "image"],
        help="Force the layer type instead of auto-detecting it",
    )
    parser.add_argument(
        "--lut", type=str, default=None, dest="lut_path",
        help="Path to a FreeSurfer-style LUT (id name r g b a per line). "
             "Defaults to a same-basename .txt next to nii_file if present.",
    )
    parser.add_argument(
        "--chunk_size", type=int, nargs=3, default=[64, 64, 64],
        help="Precomputed chunk size (x y z), in voxels",
    )
    parser.add_argument(
        "--encoding", type=str, default=None,
        help='CloudVolume encoding (default: "raw")',
    )
    parser.add_argument(
        "--mesh", action="store_true", dest="with_mesh",
        help="Build meshes via igneous (segmentation layers only)",
    )
    parser.add_argument("--mesh_mip", type=int, default=0)
    parser.add_argument("--mesh_shape", type=int, nargs=3, default=[448, 448, 448])
    parser.add_argument("--dust_threshold", type=int, default=None)
    parser.add_argument("--parallel", type=int, default=1)
    parser.add_argument(
        "--skip_segment_properties", action="store_true",
        help="Skip writing segment_properties/segment_colors.json",
    )
    parser.add_argument("--background_id", type=int, default=0)

    args = parser.parse_args()
    main(
        args.nii_file, args.output_dir, args.layer_type, args.lut_path,
        args.chunk_size, args.encoding, args.with_mesh, args.mesh_mip,
        args.mesh_shape, args.dust_threshold, args.parallel,
        args.skip_segment_properties, args.background_id,
    )
