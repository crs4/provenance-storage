import json
from minio import Minio

client = Minio("localhost:9000", "minio", "miniosecret", secure=False)
client.make_bucket("bucket01")
assert client.list_buckets() == ["bucket01"]
client.fput_object("bucket01", "README.md", "README.md")
# anonymous read-only policy, see https://github.com/minio/minio-py/blob/88f4244fe89fb9f23de4f183bdf79524c712deaa/examples/set_bucket_policy.py#L27
policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"AWS": "*"},
            "Action": ["s3:GetBucketLocation", "s3:ListBucket"],
            "Resource": "arn:aws:s3:::bucket01",
        },
        {
            "Effect": "Allow",
            "Principal": {"AWS": "*"},
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::bucket01/*",
        },
    ],
}
client.set_bucket_policy("bucket01", json.dumps(policy))
client.remove_object("bucket01", "README.md")
client.remove_bucket("bucket01")
