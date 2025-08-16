from provstor_api.utils.queries import (
    ACTIONS_FOR_RESULT_QUERY,
    OBJECTS_FOR_ACTION_QUERY,
    RESULTS_FOR_ACTION_QUERY
)
from provstor_api.utils.query import run_query


def fetch_actions_for_result(result_id):
    query_res = run_query(ACTIONS_FOR_RESULT_QUERY % result_id)
    output = [str(_[0]) for _ in query_res]
    return {"result": output}

def fetch_objects_for_action(action_id):
    query_res = run_query(OBJECTS_FOR_ACTION_QUERY % {"action": action_id})
    output = [str(_[0]) for _ in query_res]
    return {"result": output}

def fetch_results_for_action(action_id):
    query_res = run_query(RESULTS_FOR_ACTION_QUERY % {"action": action_id})
    output = [str(_[0]) for _ in query_res]
    return {"result": output}