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


from provstor_api.utils.queries import (
    ACTIONS_FOR_RESULT_QUERY,
    OBJECTS_FOR_ACTION_QUERY,
    RESULTS_FOR_ACTION_QUERY
)
from provstor_api.utils.query import run_query


def fetch_actions_for_result(result_id):
    query_res = run_query(ACTIONS_FOR_RESULT_QUERY % result_id)
    return [str(_[0]) for _ in query_res]


def fetch_objects_for_action(action_id):
    query_res = run_query(OBJECTS_FOR_ACTION_QUERY % {"action": action_id})
    return [str(_[0]) for _ in query_res]


def fetch_results_for_action(action_id):
    query_res = run_query(RESULTS_FOR_ACTION_QUERY % {"action": action_id})
    return [str(_[0]) for _ in query_res]
