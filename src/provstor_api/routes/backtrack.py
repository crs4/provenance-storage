from fastapi import APIRouter, HTTPException
from provstor_api.utils.get_utils import (
    fetch_actions_for_result, fetch_objects_for_action, fetch_results_for_action
)

router = APIRouter()


@router.get("/")
def backtrack(result_id: str):
    try:
        actions = list(fetch_actions_for_result(result_id)["result"])
        if not actions:
            raise HTTPException(status_code=404, detail="No actions found for the given result")
        for a in actions:
            objects = list(fetch_objects_for_action(a)["result"])
            results = list(fetch_results_for_action(a)["result"])
            yield a, objects, results
            for obj in objects:
                for r_a, r_obj, r_res in backtrack(obj):
                    yield r_a, r_obj, r_res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
