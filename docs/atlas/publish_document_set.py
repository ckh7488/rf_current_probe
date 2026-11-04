"""Export the allowlisted RFCP showcase to the existing ATLAS report."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "viewer_A05"))
from publish_atlas_showcase import publish

if __name__ == "__main__":
    publish()
