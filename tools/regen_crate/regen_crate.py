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
import json
import os
import shutil

from rocrate.rocrate import ROCrate
from rocrate.utils import as_list


def as_file_uri(id_, crate_path):
    return "file://" + str((crate_path / id_).resolve())


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
    print("pipeline-generated outputs:", len(results))
    results_map = {_.id.rstrip("/"): _ for _ in results}
    for t in sorted([(e.type, id_) for id_, e in results_map.items()]):
        print(" ", t)
    return results_map


def copy_files(in_crate_path, out_crate_path, results_map):
    out_crate_path.mkdir(parents=True, exist_ok=True)
    for root, dirs, files in os.walk(in_crate_path):
        root = Path(root)
        out_root = out_crate_path / root.relative_to(in_crate_path)
        exclude = []
        for name in dirs:
            in_path = root / name
            if str(in_path.relative_to(in_crate_path)) in results_map:
                exclude.append(name)
                print("EXCLUDING DIR", in_path.relative_to(in_crate_path))
        dirs[:] = [_ for _ in dirs if _ not in exclude]
        for name in files:
            in_path = root / name
            if str(in_path.relative_to(in_crate_path)) not in results_map:
                out_path = out_root / name
                out_root.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(in_path, out_path)
            else:
                print("EXCLUDING FILE", in_path.relative_to(in_crate_path))


def regen_metadata(in_crate_path, out_crate_path, results_map):
    with open(in_crate_path / "ro-crate-metadata.json") as f:
        metadata = json.load(f)
    for entity in metadata["@graph"]:
        if entity["@id"] in results_map:
            entity["@id"] = as_file_uri(entity["@id"], in_crate_path)
        for k, values in entity.items():
            if k.startswith("@"):
                continue
            if isinstance(values, dict) and values["@id"] in results_map:
                entity[k]["@id"] = as_file_uri(values["@id"], in_crate_path)
            elif isinstance(values, list):
                for i, v in enumerate(values):
                    if isinstance(v, dict) and v["@id"] in results_map:
                        entity[k][i]["@id"] = as_file_uri(v["@id"], in_crate_path)
    with open(out_crate_path / "ro-crate-metadata.json", "w") as f:
        json.dump(metadata, f, indent=4)


def main(args):
    in_crate_path = Path(args.in_crate)
    out_crate_path = Path(args.out_crate)
    results_map = get_results(in_crate_path)
    copy_files(in_crate_path, out_crate_path, results_map)
    regen_metadata(in_crate_path, out_crate_path, results_map)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("in_crate", metavar="IN_RO_CRATE",
                        help="Input RO-Crate directory")
    parser.add_argument("out_crate", metavar="OUT_RO_CRATE",
                        help="Output RO-Crate directory")
    main(parser.parse_args())
