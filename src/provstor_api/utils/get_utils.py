from utils.queries import (
    ACTIONS_FOR_RESULT_QUERY,
    OBJECTS_FOR_ACTION_QUERY,
    RESULTS_FOR_ACTION_QUERY
)
from utils.query import run_query


def fetch_actions_for_result(result_id):
    query_res = run_query(ACTIONS_FOR_RESULT_QUERY % result_id)
    return [str(_[0]) for _ in query_res]


def fetch_objects_for_action(action_id):
    query_res = run_query(OBJECTS_FOR_ACTION_QUERY % {"action": action_id})
    return [str(_[0]) for _ in query_res]


def fetch_results_for_action(action_id):
    query_res = run_query(RESULTS_FOR_ACTION_QUERY % {"action": action_id})
    return [str(_[0]) for _ in query_res]
