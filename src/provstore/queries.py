RDE_QUERY = """\
PREFIX schema: <http://schema.org/>

SELECT ?rde
WHERE {
  ?md a schema:CreativeWork .
  FILTER(contains(str(?md), "ro-crate-metadata.json")) .
  ?md schema:about ?rde
}
"""
