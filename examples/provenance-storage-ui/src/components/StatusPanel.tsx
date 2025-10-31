import { useState } from "react";
import { Section } from "./UI/Section";
import { Pill } from "./UI/Pill";
import { Row } from "./UI/Row";
import { Button } from "./UI/Button";
import { Input } from "./UI/Input";
import { fetchJSON } from "../utils/api";

interface StatusPanelProps {
  api: ReturnType<typeof import("../utils/api").buildApiEndpoints>;
  baseUrl: string;
  setBaseUrl: (v: string) => void;
  setBusy: (b: boolean) => void;
  toast: string | null;
  setToast: (t: string | null) => void;
}

export function StatusPanel({ api, baseUrl, setBaseUrl, setBusy, toast, setToast }: StatusPanelProps) {
  const [status, setStatus] = useState<any>(null);

  async function checkStatus() {
    setBusy(true);
    try {
      const data = await fetchJSON(api.status);
      setStatus(data);
      setToast("API OK");
    } catch (e: any) {
      setStatus(null);
      setToast("Status error: " + e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Section title="Connection"
      right={<Button onClick={checkStatus}>Check Status</Button>}
    >
      <Row label="API base URL">
        <div className="flex gap-2">
          <Input value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} placeholder="http://host:port" />
        </div>
      </Row>
      <div className="text-sm text-gray-600">Make sure your backend enables CORS for this origin.</div>
      {status && (
        <pre className="mt-3 p-3 bg-gray-100 rounded-xl text-xs overflow-auto">{JSON.stringify(status, null, 2)}</pre>
      )}
      {toast && <Pill>{toast}</Pill>}
    </Section>
  );
}
