# Copyright © 2024-2026 CRS4
# Copyright © 2025-2026 BSC
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

from fastapi import APIRouter
from provstor_api.utils.get_utils import (
    fetch_actions_for_result, fetch_objects_for_action, fetch_results_for_action
)

router = APIRouter()


def _backtrack_recursive(result_id, visited=None):
    if visited is None:
        visited = set()

    if result_id in visited:
        return []

    visited.add(result_id)
    results = []

    actions = fetch_actions_for_result(result_id)
    for a in actions:
        objects = fetch_objects_for_action(a)
        action_results = fetch_results_for_action(a)
        results.append({
            "action": a,
            "objects": objects,
            "results": action_results
        })

        for obj in objects:
            nested_results = _backtrack_recursive(obj, visited)
            results.extend(nested_results)

    return results


@router.get("/")
def backtrack_fn(result_id: str):
    backtrack_results = _backtrack_recursive(result_id)
    return {"result": backtrack_results}
