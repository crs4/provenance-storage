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

from .get import (
    get_actions_for_result,
    get_objects_for_action,
    get_results_for_action
)


def backtrack(result_id):
    actions = list(get_actions_for_result(result_id))
    for a in actions:
        objects = list(get_objects_for_action(a))
        results = list(get_results_for_action(a))
        yield a, objects, results
        for obj in objects:
            for r_a, r_obj, r_res in backtrack(obj):
                yield r_a, r_obj, r_res
