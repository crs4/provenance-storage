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

"""\
Regenerate an nf-prov WRROC, linking pipeline outputs as file:// URIs.
"""

from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil

from rocrate.rocrate import ROCrate
from rocrate.utils import as_list, iso_now

CHUNK_SIZE = 16384
WRROC_CONTEXT = "https://w3id.org/ro/terms/workflow-run/context"


def as_file_uri(id_, crate_path):
    if id_.startswith("file:/"):
        return id_
    return "file://" + str((crate_path / id_).resolve())


def sha256sum(path):
    m = hashlib.sha256()
    size = 0
    with open(path, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            m.update(chunk)
            size += len(chunk)
    return m.hexdigest(), size


def get_results(in_crate_path):
    in_crate = ROCrate(in_crate_path)
    all_actions = [_ for _ in in_crate.contextual_entities
                   if _.type == "CreateAction"]
    wf = in_crate.root_dataset["mainEntity"]
    sel = [_ for _ in all_actions if _["instrument"] is wf]
    assert len(sel) == 1
    wf_action = sel[0]
    other_actions = [_ for _ in all_actions if _ is not wf_action]
    results = sum([as_list(_.get("result", [])) for _ in other_actions], [])
    # in nf-prov, intermediate output ids have a leading "#"
    results = set([_ for _ in results if not _.id.startswith("#")])
    assert results == set(wf_action["result"])
    return set([_.id.rstrip("/") for _ in results])


def copy_files(in_crate_path, out_crate_path, results):
    out_crate_path.mkdir(parents=True, exist_ok=True)
    for root, dirs, files in os.walk(in_crate_path):
        root = Path(root)
        out_root = out_crate_path / root.relative_to(in_crate_path)
        exclude = []
        for name in dirs:
            in_path = root / name
            if str(in_path.relative_to(in_crate_path)) in results:
                exclude.append(name)
                print("Excluding dir:", in_path.relative_to(in_crate_path))
        dirs[:] = [_ for _ in dirs if _ not in exclude]
        for name in files:
            in_path = root / name
            if str(in_path.relative_to(in_crate_path)) not in results:
                out_path = out_root / name
                out_root.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(in_path, out_path)
            else:
                print("Excluding file:", in_path.relative_to(in_crate_path))


def regen_metadata(in_crate_path, out_crate_path, results, checksums=False):
    with open(in_crate_path / "ro-crate-metadata.json") as f:
        metadata = json.load(f)
    context = as_list(metadata["@context"])
    if WRROC_CONTEXT not in context:
        metadata["@context"] = context + [WRROC_CONTEXT]
    for entity in metadata["@graph"]:
        if entity["@id"] in results or entity["@id"].startswith("file:/"):
            if checksums:
                if entity["@id"].startswith("file:/"):
                    path = Path(entity["@id"].split(":", 1)[-1])
                else:
                    path = in_crate_path / entity["@id"]
                if path.is_file():
                    print("computing sha256 checksum:", entity["@id"])
                    cs, size = sha256sum(path)
                    entity["sha256"] = cs
                    entity["contentSize"] = size
            entity["@id"] = as_file_uri(entity["@id"], in_crate_path)
            entity["sdDatePublished"] = iso_now()
        for k, values in entity.items():
            if k.startswith("@"):
                continue
            if isinstance(values, dict) and values["@id"] in results:
                entity[k]["@id"] = as_file_uri(values["@id"], in_crate_path)
            elif isinstance(values, list):
                for i, v in enumerate(values):
                    if isinstance(v, dict) and v["@id"] in results:
                        entity[k][i]["@id"] = as_file_uri(v["@id"], in_crate_path)
    with open(out_crate_path / "ro-crate-metadata.json", "w") as f:
        json.dump(metadata, f, indent=4)


def main(args):
    in_crate_path = Path(args.in_crate)
    out_crate_path = Path(args.out_crate)
    results = get_results(in_crate_path)
    copy_files(in_crate_path, out_crate_path, results)
    regen_metadata(in_crate_path, out_crate_path, results, args.checksums)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("in_crate", metavar="IN_RO_CRATE",
                        help="Input RO-Crate directory")
    parser.add_argument("out_crate", metavar="OUT_RO_CRATE",
                        help="Output RO-Crate directory")
    parser.add_argument("--checksums", action="store_true",
                        help="add checksums of excluded files to the metadata")
    main(parser.parse_args())
