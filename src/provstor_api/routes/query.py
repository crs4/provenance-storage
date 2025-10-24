# Copyright © 2024-2025 CRS4
# Copyright © 2025 BSC
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


from fastapi import APIRouter, UploadFile

from provstor_api.utils.query import run_query
from provstor_api.utils.queries import GRAPHS_QUERY, RDE_GRAPH_QUERY

router = APIRouter()


@router.get("/list-graphs/")
def list_graphs():
    query_res = run_query(GRAPHS_QUERY)
    output = [item[0] for item in query_res]
    return {"result": output}


@router.get("/list-RDE-graphs/")
def list_rde_graphs():
    query_res = run_query(RDE_GRAPH_QUERY)
    output = [item for item in query_res]
    return {"result": output}


@router.post("/run-query/")
async def run_query_sparql(query_file: UploadFile, graph: str = None):
    content = await query_file.read()
    query = content.decode("utf-8")
    query_res = run_query(query, graph)
    result_list = [item for item in query_res]
    return {"result": result_list}
