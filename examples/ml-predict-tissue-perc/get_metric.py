import argparse

import numpy as np
import zarr


TISSUE_THRESHOLD = 50


def main(args):
    store = zarr.storage.ZipStore(args.zarr_path, read_only=True)
    group = zarr.open_group(store, mode='r')
    assert "tissue_high" in group
    array = np.array(group["tissue_high"])
    array[array < TISSUE_THRESHOLD] = 0
    array[array >= TISSUE_THRESHOLD] = 1
    p = 100 * np.count_nonzero(array) / array.size
    print(p)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("zarr_path", metavar="ZARR_PATH",
                        help="Path to the Zarr tissue_high array")
    main(parser.parse_args())
