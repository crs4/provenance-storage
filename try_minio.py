
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


import json
import shutil

from minio import Minio


BUCKET = "crates"

client = Minio("localhost:9000", "minio", "miniosecret", secure=False)
if not client.bucket_exists(BUCKET):
    client.make_bucket(BUCKET)
print("buckets:", client.list_buckets())

for crate in "crate1", "crate2":
    shutil.make_archive(crate, "zip", crate)
    zipped_crate = f"{crate}.zip"
    client.fput_object(BUCKET, zipped_crate, zipped_crate)

# anonymous read-only policy, see https://github.com/minio/minio-py/blob/88f4244fe89fb9f23de4f183bdf79524c712deaa/examples/set_bucket_policy.py#L27
policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"AWS": "*"},
            "Action": ["s3:GetBucketLocation", "s3:ListBucket"],
            "Resource": f"arn:aws:s3:::{BUCKET}",
        },
        {
            "Effect": "Allow",
            "Principal": {"AWS": "*"},
            "Action": "s3:GetObject",
            "Resource": f"arn:aws:s3:::{BUCKET}/*",
        },
    ],
}
client.set_bucket_policy(BUCKET, json.dumps(policy))
# now the bucket's objects are accessible via http as:
#   http://localhost:9000/BUCKET/OBJECT
# e.g. curl -o crate1.zip http://localhost:9000/crates/crate1.zip

# client.remove_object(BUCKET, "crate1.zip")
# client.remove_object(BUCKET, "crate2.zip")
# client.remove_bucket(BUCKET)
