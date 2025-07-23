from . import logger
from .utils.io import list_h5_names
from .utils.parsers import parse_image_lists
from pathlib import Path
import argparse
import collections.abc as collections
from pathlib import Path
from typing import List, Optional, Union
import os


def generate_pairs(names: List[str], window_size: int = 2, loop: bool = False) -> List[tuple]:
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
        n_images = len(camera_images)
        
        # Generate pairs within the same camera
        for j in range(n_images):
            current_img = camera_images[j]
            
            # Loop through potential future frames based on window_size
            for k_offset in range(1, window_size + 1):
                # Calculate the index for the candidate image
                k = (j + k_offset) % n_images # Use modulo for looping
                
                # If looping is enabled, or if k is within the bounds (no loop)
                if loop or (j + k_offset < n_images):
                    candidate_img = camera_images[k]
                    pairs.append((current_img, candidate_img))
            
            # Generate pairs with other cameras
            for other_camera_id in camera_ids[i + 1:]:
                other_images = cameras[other_camera_id]
                n_other_images = len(other_images)
                
                # Get current frame number
                current_frame = int(current_img.split('/')[-1].split('.')[0])
                
                # Match with frames from current to current+window_size in other camera
                for other_j in range(n_other_images):
                    other_img = other_images[other_j]
                    other_frame = int(other_img.split('/')[-1].split('.')[0])
                    
                    # Calculate frame difference, considering looping if enabled
                    frame_diff = other_frame - current_frame
                    if loop:
                        # Consider circular difference for looping
                        if abs(frame_diff) <= window_size:
                            pass # direct match
                        elif current_frame > other_frame:
                            # if current frame is later than other frame, check if other frame is near the end
                            if n_images > 0 and (current_frame - (other_frame + n_images)) <= window_size:
                                frame_diff = current_frame - (other_frame + n_images)
                            elif n_other_images > 0 and (current_frame - (other_frame + n_other_images)) <= window_size:
                                frame_diff = current_frame - (other_frame + n_other_images)

                        elif current_frame < other_frame:
                            # if other frame is later than current frame, check if current frame is near the end
                            if n_images > 0 and ((current_frame + n_images) - other_frame) <= window_size:
                                frame_diff = (current_frame + n_images) - other_frame
                            elif n_other_images > 0 and ((current_frame + n_other_images) - other_frame) <= window_size:
                                frame_diff = (current_frame + n_other_images) - other_frame
                    
                    if 0 <= frame_diff <= window_size:
                        pairs.append((current_img, other_img))
    
    return pairs


def main(
    output: Path,
    image_list: Optional[Union[Path, List[str]]] = None,
    features: Optional[Path] = None,
    window_size: int = 2,
    loop: bool = False, 
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

    # Generate pairs with window constraint and loop flag
    pairs = generate_pairs(names, window_size, loop)

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
    parser.add_argument("--loop", action="store_true",
                        help="Allow matching first frame with last frame and so on (circular matching).") # Add loop argument
    args = parser.parse_args()
    main(**args.__dict__)