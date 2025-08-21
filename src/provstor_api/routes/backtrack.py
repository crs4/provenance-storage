from fastapi import APIRouter, HTTPException
from utils.get_utils import (
    fetch_actions_for_result, fetch_objects_for_action, fetch_results_for_action
)
from utils.queries import GRAPH_ID_FOR_FILE_QUERY, WFRUN_RESULTS_QUERY
from utils.query import run_query

router = APIRouter()


def _backtrack_recursive(result_id, visited=None):
    if visited is None:
        visited = set()

    if result_id in visited:
        return []

    visited.add(result_id)
    results = []

    try:
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

    except Exception:
        pass  # Handle gracefully if no actions found

    return results


@router.get("/")
def backtrack_fn(file_uri: str = None, result_id: str = None):
    try:
        target_result_id = result_id

        if file_uri and not result_id:
            graphs = run_query(GRAPH_ID_FOR_FILE_QUERY % file_uri)
            if not graphs:
                raise HTTPException(status_code=404, detail="No graphs found for the given file")

            graph_id = str(list(graphs)[0][0])
            results = run_query(WFRUN_RESULTS_QUERY, graph_id=graph_id)
            if not results:
                raise HTTPException(status_code=404, detail="No results found for the file")

            target_result_id = str(list(results)[0][0])

        if not target_result_id:
            raise HTTPException(status_code=400, detail="Either file_uri or result_id must be provided")

        backtrack_results = _backtrack_recursive(target_result_id)

        if not backtrack_results:
            raise HTTPException(status_code=404, detail="No backtrack results found")

        return {"result": backtrack_results}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
