from fastapi import APIRouter, UploadFile, HTTPException
from provstor_api.utils.query import run_query
from provstor_api.utils.queries import GRAPHS_QUERY, RDE_GRAPH_QUERY
import logging

router = APIRouter()


@router.get("/list-graphs/")
def list_graphs():
    try:
        query_res = run_query(GRAPHS_QUERY)
        output = []
        for (i, item) in zip(range(len(query_res)), query_res):
            output.append(item[0])
        return {"result": output}
    except Exception as e:
        logging.error(f"Error fetching graphs: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to fetch graphs: {str(e)}")


@router.get("/list-RDE-graphs/")
def list_rde_graphs():
    try:
        query_res = run_query(RDE_GRAPH_QUERY)
        output = [item for item in query_res]
        return {"result": output}
    except Exception as e:
        logging.error(f"Error fetching RDE IDs: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to fetch RDE IDs: {str(e)}")


@router.post("/run-query/")
async def run_query_sparql(query_file: UploadFile, graph: str = None):
    try:
        content = await query_file.read()
        query = content.decode("utf-8")
        print(f"Query:\n{query}\n")
        query_res = run_query(query, graph)
        result_list = [item.toPython() if hasattr(item, 'toPython') else item for item in query_res]
        return {"result": result_list}
    except Exception as e:
        logging.error(f"Error processing SPARQL query: {e}")
        raise HTTPException(status_code=400, detail=f"Query failed: {str(e)}")

