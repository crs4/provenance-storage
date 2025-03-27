# Copyright © 2024-2025 CRS4
#
# This file is part of ProvStor.
#
# ProvStor is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# ProvStor is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ProvStor. If not, see <https://www.gnu.org/licenses/>.

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
