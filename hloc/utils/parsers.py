import logging
from collections import defaultdict
from pathlib import Path
import os
import numpy as np
import pycolmap

logger = logging.getLogger(__name__)


def parse_image_list(path, with_intrinsics=False):
    images = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip("\n")
            if len(line) == 0 or line[0] == "#":
                continue
            name, *data = line.split()
            if with_intrinsics:
                model, width, height, *params = data
                params = np.array(params, float)
                cam = pycolmap.Camera(
                    model=model, width=int(width), height=int(height), params=params
                )
                images.append((name, cam))
            else:
                images.append(name)

    assert len(images) > 0
    logger.info(f"Imported {len(images)} images from {path.name}")
    return images


def parse_image_lists(directory):
    """
    Lists all files in a directory and its subdirectories.
    
    Args:
        directory (str): Path to the directory to scan
    
    Returns:
        list: List of all file paths found
    """
    # Convert the directory path to a Path object
    dir_path = Path(directory)
    
    # List to store all file paths
    all_files = []
    
    try:
        # Walk through directory and subdirectories
        for root, dirs, files in os.walk(dir_path):
            # Create Path object for current directory
            current_dir = Path(root)
            
            # Add each file with its full path
            for file in files:
                file_path = current_dir / file
                # Convert to string and make it relative to the starting directory
                relative_path = str(file_path.relative_to(dir_path))
                all_files.append(relative_path)
                
        return sorted(all_files)  # Return sorted list for better readability
        
    except Exception as e:
        print(f"Error scanning directory: {e}")
        return []


def parse_retrieval(path):
    retrieval = defaultdict(list)
    with open(path, "r") as f:
        for p in f.read().rstrip("\n").split("\n"):
            if len(p) == 0:
                continue
            q, r = p.split()
            retrieval[q].append(r)
    return dict(retrieval)


def names_to_pair(name0, name1, separator="/"):
    return separator.join((name0.replace("/", "-"), name1.replace("/", "-")))


def names_to_pair_old(name0, name1):
    return names_to_pair(name0, name1, separator="_")
