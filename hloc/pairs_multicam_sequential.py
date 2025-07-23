from . import logger
from .utils.io import list_h5_names
from .utils.parsers import parse_image_lists
from pathlib import Path
import argparse
import collections.abc as collections
from pathlib import Path
from typing import List, Optional, Union
import os


    
def generate_pairs(names: List[str], window_size: int = 2) -> List[tuple]:
    # Parse and organize images by camera
    cameras = {}
    for name in names:
        # Skip files that don't match our expected format
        try:
            split_name = name.split('/')
            
            # The camera ID is assumed to be the parent directory of the image file.
            # This supports both 'cam/frame.ext' and 'rig/cam/frame.ext' formats.
            camera_id = split_name[-2]
            # Verify this is a valid frame by attempting to convert to int
            frame_num = int(split_name[-1].split('.')[0])
            if camera_id not in cameras:
                cameras[camera_id] = []
            cameras[camera_id].append(name)
        except (ValueError, IndexError):
            logger.warning(f"Skipping invalid image name: {name}")
            continue
    
    # Sort images within each camera
    for camera_id in cameras:
        cameras[camera_id].sort()
    
    camera_ids = sorted(cameras.keys())
    pairs = []
    
    # Process each camera
    for i, camera_id in enumerate(camera_ids):
        camera_images = cameras[camera_id]
        
        # Generate pairs within the same camera
        for j in range(len(camera_images)):
            current_img = camera_images[j]
            # Match with future frames up to window_size
            for k in range(j + 1, min(j + window_size + 1, len(camera_images))):
                pairs.append((current_img, camera_images[k]))
            
            # Generate pairs with other cameras
            for other_camera_id in camera_ids[i + 1:]:
                other_images = cameras[other_camera_id]
                # Get current frame number
                current_frame = int(current_img.split('/')[-1].split('.')[0])
                
                # Match with frames from current to current+window_size in other camera
                for other_img in other_images:
                    other_frame = int(other_img.split('/')[-1].split('.')[0])
                    if current_frame <= other_frame <= current_frame + window_size:
                        pairs.append((current_img, other_img))
    
    return pairs

def main(
    output: Path,
    image_list: Optional[Union[Path, List[str]]] = None,
    features: Optional[Path] = None,
    ref_list: Optional[Union[Path, List[str]]] = None,
    ref_features: Optional[Path] = None,
    window_size: int = 2,
):
    if image_list is not None:
        if isinstance(image_list, (str, Path)):
            names = parse_image_lists(image_list)
        elif isinstance(image_list, collections.Iterable):
            names = list(image_list)
        else:
            raise ValueError(f"Unknown type for image list: {image_list}")
    elif features is not None:
        names = list_h5_names(features)
    else:
        raise ValueError("Provide either a list of images or a feature file.")

    # Generate pairs with window constraint
    pairs = generate_pairs(names, window_size)

    logger.info(f"Found {len(pairs)} pairs.")
    with open(output, "w") as f:
        f.write("\n".join(" ".join([i, j]) for i, j in pairs))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--image_list", type=Path)
    parser.add_argument("--features", type=Path)
    parser.add_argument("--window_size", type=int, default=2,
                      help="Number of future frames to include in pairs")
    args = parser.parse_args()
    main(**args.__dict__)