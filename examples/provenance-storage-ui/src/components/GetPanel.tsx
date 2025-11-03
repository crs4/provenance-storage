import { useState } from "react";
import { Section } from "./UI/Section";
import { Row } from "./UI/Row";
import { Button } from "./UI/Button";
import { Input } from "./UI/Input";
import { Pill } from "./UI/Pill";
import { fetchJSON } from "../utils/api";

interface GetPanelProps {
  api: ReturnType<typeof import("../utils/api").buildApiEndpoints>;
  setBusy: (b: boolean) => void;
  toast: string | null;
  setToast: (t: string | null) => void;
}

type GetEndpoint =
  | "getWorkflow"
  | "getRunResults"
  | "getRunObjects"
  | "getRunParams"
  | "getGraphsForResult"
  | "getObjectsForResult"
  | "getActionsForResult"
  | "getGraphsForFile"
  | "getResultsForAction"
  | "getObjectsForAction";


export function GetPanel({ api, setBusy, toast, setToast }: GetPanelProps) {
  const [graphId, setGraphId] = useState("");
  const [resultId, setResultId] = useState("");
  const [fileId, setFileId] = useState("");
  const [actionId, setActionId] = useState("");
  const [simpleResult, setSimpleResult] = useState<any>(null);

  async function callGet(endpoint: GetEndpoint) {
    setBusy(true);
    try {
      let url = new URL((api as any)[endpoint]);
      switch (endpoint) {
        case "getWorkflow":
        case "getRunResults":
        case "getRunObjects":
        case "getRunParams":
          if (!graphId) throw new Error("graph_id required");
          url.searchParams.set("graph_id", graphId);
          break;
        case "getGraphsForResult":
        case "getObjectsForResult":
        case "getActionsForResult":
          if (!resultId) throw new Error("result_id required");
          url.searchParams.set("result_id", resultId);
          break;
        case "getGraphsForFile":
          if (!fileId) throw new Error("file_id required");
          url.searchParams.set("file_id", fileId);
          break;
        case "getResultsForAction":
        case "getObjectsForAction":
          if (!actionId) throw new Error("action_id required");
          url.searchParams.set("action_id", actionId);
          break;
        default:
          break;
      }
      const data = await fetchJSON(url.toString());
      setSimpleResult(data?.result ?? data);
      setToast("Done");
    } catch (e: any) {
      setSimpleResult(null);
      setToast(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Section title="Get">
      <div className="grid md:grid-cols-2 gap-4">
        <Section title="By graph_id">
          <Row label="graph_id">
            <Input value={graphId} onChange={e => setGraphId(e.target.value)} placeholder="mycrate or http://…" />
          </Row>
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => callGet("getWorkflow")}>/get/workflow/</Button>
            <Button onClick={() => callGet("getRunResults")}>/get/run-results/</Button>
            <Button onClick={() => callGet("getRunObjects")}>/get/run-objects/</Button>
            <Button onClick={() => callGet("getRunParams")}>/get/run-params/</Button>
          </div>
        </Section>
        <Section title="By result_id">
          <Row label="result_id">
            <Input value={resultId} onChange={e => setResultId(e.target.value)} placeholder="file://… or arcp://…" />
          </Row>
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => callGet("getGraphsForResult")}>/get/graphs-for-result/</Button>
            <Button onClick={() => callGet("getObjectsForResult")}>/get/objects-for-result/</Button>
            <Button onClick={() => callGet("getActionsForResult")}>/get/actions-for-result/</Button>
          </div>
        </Section>
      </div>
      <div className="grid md:grid-cols-2 gap-4">
        <Section title="By file_id">
          <Row label="file_id (full URI)">
            <Input value={fileId} onChange={e => setFileId(e.target.value)} placeholder="file://…" />
          </Row>
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => callGet("getGraphsForFile")}>/get/graphs-for-file/</Button>
          </div>
        </Section>
        <Section title="By action_id">
          <Row label="action_id">
            <Input value={actionId} onChange={e => setActionId(e.target.value)} placeholder="arcp://…" />
          </Row>
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => callGet("getObjectsForAction")}>/get/objects-for-action/</Button>
            <Button onClick={() => callGet("getResultsForAction")}>/get/results-for-action/</Button>
          </div>
        </Section>
      </div>
      <div>
        <h3 className="font-semibold mb-2">Result</h3>
        <pre className="p-3 bg-gray-100 rounded-xl text-xs overflow-auto max-h-80">{JSON.stringify(simpleResult, null, 2)}</pre>
      </div>
      {toast && <Pill>{toast}</Pill>}
    </Section>
  );
}

