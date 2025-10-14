import { useState } from "react";
import { Section } from "./UI/Section";
import { Row } from "./UI/Row";
import { Button } from "./UI/Button";
import { Input } from "./UI/Input";
import { Pill } from "./UI/Pill";
import { downloadGET } from "../utils/api";

interface DownloadPanelProps {
  api: ReturnType<typeof import("../utils/api").buildApiEndpoints>;
  toast: string | null;
  setToast: (t: string | null) => void;
}

export function DownloadPanel({ api, toast, setToast }: DownloadPanelProps) {
  const [resultId, setResultId] = useState("");
  const [fileUri, setFileUri] = useState("");

  async function downloadCrate() {
    if (!resultId) return setToast("Set ROOT_DATA_ENTITY_ID (rde_id)");
    const url = new URL(api.getCrate);
    url.searchParams.set("rde_id", resultId);
    await downloadGET(url.toString(), resultId);
  }

  async function downloadFile() {
    if (!fileUri) return setToast("Set FILE_URI");
    const url = new URL(api.getFile);
    url.searchParams.set("file_uri", fileUri);
    await downloadGET(url.toString(), fileUri);
  }

  return (
    <Section title="Download">
      <div className="grid md:grid-cols-2 gap-4">
        <Section title="Crate">
          <Row label="result_id (rde_id)">
            <Input value={resultId} onChange={e => setResultId(e.target.value)} placeholder="file://… or arcp://…" />
          </Row>
          <Button onClick={downloadCrate}>Download crate</Button>
        </Section>
        <Section title="File">
          <Row label="file_uri (RDE URI)">
            <Input value={fileUri} onChange={e => setFileUri(e.target.value)} placeholder="arcp://…" />
          </Row>
          <Button onClick={downloadFile}>Download file</Button>
        </Section>
      </div>
      {toast && <Pill>{toast}</Pill>}
    </Section>
  );
}
