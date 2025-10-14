import { useMemo, useState } from "react";
import { buildApiEndpoints } from "./utils/api";
import { Section } from "./components/UI/Section";
import { Pill } from "./components/UI/Pill";
import { Tabs } from "./components/UI/Tabs";
import { StatusPanel } from "./components/StatusPanel";
import { UploadPanel } from "./components/UploadPanel";
import { QueryPanel } from "./components/QueryPanel";
import { BrowsePanel } from "./components/BrowsePanel";
import { GetPanel } from "./components/GetPanel";
import { DownloadPanel } from "./components/DownloadPanel";


const defaultBaseUrl = (typeof window !== "undefined" && localStorage.getItem("provstor_base_url")) || "http://localhost:8000";


// =====================
// Main Component
// =====================
export default function ProvStorUI() {
  const [baseUrl, setBaseUrl] = useState<string>(defaultBaseUrl);
  const [tab, setTab] = useState<"status" | "upload" | "query" | "browse" | "get" | "download">("status");
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const api = useMemo(() => buildApiEndpoints(baseUrl), [baseUrl]);

  const setAndSaveBaseUrl = (v: string) => {
    setBaseUrl(v);
    if (typeof window !== "undefined") localStorage.setItem("provstor_base_url", v);
  };

  return (
    <div className="flex justify-center min-h-screen bg-gray-50">
      <div className="max-w-6xl w-full mx-auto p-6 flex justify-center">
        <div className="w-full max-w-6xl">
          <Section title="ProvStor Web UI"
            right={<div className="flex items-center gap-2"><Pill>{busy ? "Working…" : "Idle"}</Pill>{toast && <Pill>{toast}</Pill>}</div>}
          >
            <div className="mb-4 text-sm text-gray-600">Interact with your store without the CLI.</div>
            <StatusPanel
              api={api}
              baseUrl={baseUrl}
              setBaseUrl={setAndSaveBaseUrl}
              setBusy={setBusy}
              toast={toast}
              setToast={setToast}
            />
            <Tabs
              value={tab}
              onChange={setTab}
              tabs={[
                { value: "browse", label: "Browse Graphs" },
                { value: "query", label: "Query" },
                { value: "get", label: "Get" },
                { value: "download", label: "Download" },
                { value: "upload", label: "Upload Crate" },
              ]}
            />
            {tab === "upload" && (
              <UploadPanel
                api={api}
                setBusy={setBusy}
                toast={toast}
                setToast={setToast}
              />
            )}
            {tab === "query" && (
              <QueryPanel
                api={api}
                setBusy={setBusy}
                toast={toast}
                setToast={setToast}
              />
            )}
            {tab === "browse" && (
              <BrowsePanel
                api={api}
                setBusy={setBusy}
                toast={toast}
                setToast={setToast}
              />
            )}
            {tab === "get" && (
              <GetPanel
                api={api}
                setBusy={setBusy}
                toast={toast}
                setToast={setToast}
              />
            )}
            {tab === "download" && (
              <DownloadPanel
                api={api}
                toast={toast}
                setToast={setToast}
              />
            )}
            <footer className="text-xs text-gray-500 mt-6">
              Backend endpoints inferred from your CLI (upload, query, get/*). Ensure CORS is enabled on the API.
            </footer>
          </Section>
        </div>
      </div>
    </div>
  );
}
