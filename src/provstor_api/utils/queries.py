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


RDE_QUERY = """\
PREFIX schema: <http://schema.org/>

SELECT DISTINCT ?rde
WHERE {
  ?md a schema:CreativeWork .
  FILTER(contains(str(?md), "ro-crate-metadata.json")) .
  ?md schema:about ?rde
}
"""

# The parameter must be replaced by a root data entity id
CRATE_URL_QUERY = """\
PREFIX schema: <http://schema.org/>

SELECT DISTINCT ?crate_url
WHERE {
  <%s> schema:url ?crate_url
}
"""


GRAPH_ID_FOR_FILE_QUERY = """\
PREFIX schema: <http://schema.org/>

SELECT DISTINCT ?url
WHERE {
  ?md a schema:CreativeWork .
  FILTER(contains(str(?md), "ro-crate-metadata.json")) .
  ?md schema:about ?rde .
  ?rde schema:url ?url .
  ?rde schema:hasPart <%s> .
}
"""


GRAPH_ID_FOR_RESULT_QUERY = """\
PREFIX schema: <http://schema.org/>

SELECT DISTINCT ?url
WHERE {
  ?md a schema:CreativeWork .
  FILTER(contains(str(?md), "ro-crate-metadata.json")) .
  ?md schema:about ?rde .
  ?rde schema:url ?url .
  ?rde schema:mentions ?action .
  ?action a schema:CreateAction .
  ?action schema:result <%s> .
}
"""

WORKFLOW_QUERY = """\
PREFIX schema: <http://schema.org/>

SELECT DISTINCT ?workflow
WHERE {
  ?md a schema:CreativeWork .
  FILTER(contains(str(?md), "ro-crate-metadata.json")) .
  ?md schema:about ?rde .
  ?rde schema:mainEntity ?workflow .
}
"""

WFRUN_RESULTS_QUERY = """\
PREFIX schema: <http://schema.org/>

SELECT DISTINCT ?result
WHERE {
  ?md a schema:CreativeWork .
  FILTER(contains(str(?md), "ro-crate-metadata.json")) .
  ?md schema:about ?rde .
  ?rde schema:mainEntity ?workflow .
  ?action schema:instrument ?workflow .
  ?action schema:result ?result .
  { ?result a schema:MediaObject } UNION { ?result a schema:Dataset }
}
"""

WFRUN_OBJECTS_QUERY = """\
PREFIX schema: <http://schema.org/>

SELECT DISTINCT ?object
WHERE {
  ?md a schema:CreativeWork .
  FILTER(contains(str(?md), "ro-crate-metadata.json")) .
  ?md schema:about ?rde .
  ?rde schema:mainEntity ?workflow .
  ?action schema:instrument ?workflow .
  ?action schema:object ?object .
  { ?object a schema:MediaObject } UNION { ?object a schema:Dataset }
}
"""


ACTIONS_FOR_RESULT_QUERY = """\
PREFIX schema: <http://schema.org/>

SELECT DISTINCT ?action
WHERE {
  ?md a schema:CreativeWork .
  FILTER(contains(str(?md), "ro-crate-metadata.json")) .
  ?md schema:about ?rde .
  ?rde schema:mentions ?action .
  ?action a schema:CreateAction .
  ?action schema:result <%s> .
}
"""


OBJECTS_FOR_ACTION_QUERY = """\
PREFIX schema: <http://schema.org/>

SELECT DISTINCT ?object
WHERE {
  ?md a schema:CreativeWork .
  FILTER(contains(str(?md), "ro-crate-metadata.json")) .
  ?md schema:about ?rde .
  ?rde schema:mentions <%(action)s> .
  <%(action)s> a schema:CreateAction .
  <%(action)s> schema:object ?object .
  { ?object a schema:MediaObject } UNION { ?object a schema:Dataset }
}
"""


RESULTS_FOR_ACTION_QUERY = """\
PREFIX schema: <http://schema.org/>

SELECT DISTINCT ?result
WHERE {
  ?md a schema:CreativeWork .
  FILTER(contains(str(?md), "ro-crate-metadata.json")) .
  ?md schema:about ?rde .
  ?rde schema:mentions <%(action)s> .
  <%(action)s> a schema:CreateAction .
  <%(action)s> schema:result ?result .
  { ?result a schema:MediaObject } UNION { ?result a schema:Dataset }
}
"""


OBJECTS_FOR_RESULT_QUERY = """\
PREFIX schema: <http://schema.org/>

SELECT DISTINCT ?object
WHERE {
  ?md a schema:CreativeWork .
  FILTER(contains(str(?md), "ro-crate-metadata.json")) .
  ?md schema:about ?rde .
  ?rde schema:mentions ?action .
  ?action a schema:CreateAction .
  ?action schema:object ?object .
  ?action schema:result <%s> .
  { ?object a schema:MediaObject } UNION { ?object a schema:Dataset }
}
"""

WFRUN_PARAMS_QUERY = """\
PREFIX schema: <http://schema.org/>

SELECT ?name ?value
WHERE {
  ?md a schema:CreativeWork .
  FILTER(contains(str(?md), "ro-crate-metadata.json")) .
  ?md schema:about ?rde .
  ?rde schema:mainEntity ?workflow .
  ?action schema:instrument ?workflow .
  ?action schema:object ?object .
  ?object a schema:PropertyValue .
  ?object schema:name ?name .
  ?object schema:value ?value .
}
"""

GRAPHS_QUERY = """\
SELECT DISTINCT ?g
WHERE {
  GRAPH ?g { ?s ?p ?o }
}
ORDER BY ?g
"""

RDE_GRAPH_QUERY = """\
PREFIX schema: <http://schema.org/>

SELECT DISTINCT ?g ?rde
WHERE {
  GRAPH ?g { 
    ?md a schema:CreativeWork .
    FILTER(contains(str(?md), "ro-crate-metadata.json")) .
    ?md schema:about ?rde .
    FILTER(STRSTARTS(STR(?md), "arcp://uuid,"))
  }
}
ORDER BY ?g
"""

