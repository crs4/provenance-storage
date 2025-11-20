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

from datetime import datetime, timezone

from rocrate.model import ContextEntity, SoftwareApplication
from rocrate.rocrate import ROCrate

DEFAULT_LICENSE = "GPL-3.0"
PROFILES_BASE = "https://w3id.org/ro/wfrun"
PROFILES_VERSION = "0.5"
WRROC_CONTEXT = "https://w3id.org/ro/terms/workflow-run/context"


class CopyOrMoveCrateGenerator:

    def __init__(self, src, dest, when=None, license=None, checksum=None, size=None):
        self.src = src
        self.dest = dest
        self.license = license or DEFAULT_LICENSE
        self.when = when or datetime.now(timezone.utc).replace(microsecond=0)
        self.checksum = checksum
        self.size = size

    def add_root_metadata(self, crate, op="cp"):
        crate.root_dataset["license"] = self.license
        name = f"{op} {self.src} {self.dest}"
        crate.root_dataset["name"] = name
        crate.root_dataset["description"] = name
        profile_id = f"{PROFILES_BASE}/process/{PROFILES_VERSION}"
        profile = crate.add(ContextEntity(crate, profile_id, properties={
            "@type": "CreativeWork",
            "name": "Process Run Crate",
            "version": PROFILES_VERSION,
        }))
        crate.root_dataset["conformsTo"] = profile

    def add_action(self, crate, op="cp"):
        if op == "cp":
            instrument_id = "https://w3id.org/ro/terms/provstor#CopyTool"
        elif op == "mv":
            instrument_id = "https://w3id.org/ro/terms/provstor#MoveTool"
        else:
            raise ValueError("op must be either 'cp' or 'mv'")
        instrument_name = op
        instrument = crate.add(SoftwareApplication(crate, instrument_id, properties={
            "name": instrument_name,
            "url": {"@id": "https://www.gnu.org/software/coreutils/"}
        }))
        obj = crate.add_file(self.src)
        res = crate.add_file(self.dest)
        if self.checksum:
            crate.metadata.extra_contexts.append(WRROC_CONTEXT)
            obj["sha256"] = res["sha256"] = self.checksum
        if self.size:
            obj["contentSize"] = res["contentSize"] = self.size
        obj["sdDatePublished"] = res["sdDatePublished"] = self.when.isoformat()
        action = crate.add_action(instrument, object=obj, result=res, properties={
            "endTime": self.when.isoformat(),
        })
        crate.root_dataset["mentions"] = action

    def generate(self):
        crate = ROCrate()
        self.add_root_metadata(crate)
        self.add_action(crate)
        return crate


class CopyCrateGenerator(CopyOrMoveCrateGenerator):

    def add_root_metadata(self, crate):
        super().add_root_metadata(crate, op="cp")

    def add_action(self, crate):
        super().add_action(crate, op="cp")


class MoveCrateGenerator(CopyOrMoveCrateGenerator):

    def add_root_metadata(self, crate):
        super().add_root_metadata(crate, op="mv")

    def add_action(self, crate):
        super().add_action(crate, op="mv")
