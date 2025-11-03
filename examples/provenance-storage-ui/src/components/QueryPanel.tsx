import { useState } from "react";
// import { Section, Row, Button, Input, Textarea, Pill } from "./UI";
import { Section } from "./UI/Section";
import { Row } from "./UI/Row";
import { Button } from "./UI/Button";
import { Input } from "./UI/Input";
import { Pill } from "./UI/Pill";
import { Textarea } from "./UI/Textarea";

interface QueryPanelProps {
  api: ReturnType<typeof import("../utils/api").buildApiEndpoints>;
  setBusy: (b: boolean) => void;
  toast: string | null;
  setToast: (t: string | null) => void;
}

export function QueryPanel({ api, setBusy, toast, setToast }: QueryPanelProps) {
  const [queryText, setQueryText] = useState<string>("SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } } LIMIT 10");
  const [queryGraph, setQueryGraph] = useState<string>("");
  const [queryResult, setQueryResult] = useState<string[][] | null>(null);

  async function runQuery() {
    setBusy(true);
    try {
      const fd = new FormData();
      const blob = new Blob([queryText], { type: "text/plain" });
      fd.append("query_file", blob, "query.sparql");
      const url = new URL(api.runQuery);
      if (queryGraph) url.searchParams.set("graph", queryGraph);
      const res = await fetch(url.toString(), { method: "POST", body: fd });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setQueryResult(json?.result || []);
      setToast("Query ok");
    } catch (e: any) {
      setQueryResult(null);
      setToast("Query failed: " + e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Section title="Query">
      <Row label="Graph (optional)">
        <Input value={queryGraph} onChange={e => setQueryGraph(e.target.value)} placeholder="crate basename or URL" />
      </Row>
      <Row label="SPARQL">
        <Textarea value={queryText} onChange={e => setQueryText(e.target.value)} />
      </Row>
      <Button onClick={runQuery}>POST /query/run-query/</Button>
      {queryResult && (
        <div className="overflow-auto">
          <table className="min-w-full text-sm">
            <tbody>
              {queryResult.map((row, i) => (
                <tr key={i} className="border-b last:border-0">
                  {row.map((cell, j) => (
                    <td key={j} className="px-2 py-1 font-mono text-xs align-top">{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {toast && <Pill>{toast}</Pill>}
    </Section>
  );
}
