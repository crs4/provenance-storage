import { useState } from "react";
import { Section } from "./UI/Section";
import { Pill } from "./UI/Pill";
import { Button } from "./UI/Button";
import { FaDownload } from "react-icons/fa";
import { fetchJSON, downloadGET } from "../utils/api";


export function BrowsePanel({ api, setBusy, toast, setToast }: {
  api: ReturnType<typeof import("../utils/api").buildApiEndpoints>;
  setBusy: (b: boolean) => void;
  toast: string | null;
  setToast: (t: string | null) => void;
}) {
  const [rdeGraphs, setRdeGraphs] = useState<string[][] | null>(null);

  async function loadGraphs() {
    setBusy(true);
    try {
      const rg = await fetchJSON(api.listRDEGraphs);
      setRdeGraphs(rg?.result || []);
      setToast("Loaded graphs");
    } catch (e: any) {
      setRdeGraphs(null);
      setToast("Load failed: " + e.message);
    } finally {
      setBusy(false);
    }
  }

  async function downloadGraph(fileUri: string) {
    setBusy(true);
    try {
      const url = new URL(api.getCrate);
      url.searchParams.set("rde_id", fileUri);
      await downloadGET(url.toString(), fileUri);
      setToast("Download started");
    } catch (e: any) {
      setToast("Download failed: " + e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Section title="Browse Graphs">
      <div className="flex gap-2">
        <Button onClick={loadGraphs}>Load graphs</Button>
      </div>
      <div className="grid gap-4">
        <div>
          <h3 className="font-semibold mb-2">RDE ↔ Graph</h3>
          <div className="border rounded-xl max-h-80 overflow-auto">
            <table className="min-w-full text-xs">
              <thead className="sticky top-0 bg-white">
                <tr><th className="text-left px-2 py-1">Graph</th><th className="text-left px-2 py-1">RDE</th></tr>
              </thead>
              <tbody>
                {(rdeGraphs || []).map((row, i) => (
                  <tr key={i} className="border-t">
                    <td className="px-2 py-1 font-mono flex items-center gap-2">
                      {row?.[0] ?? ""}
                      {row?.[1] && (
                        <Button
                          title="Download graph"
                          onClick={() => downloadGraph(row[1])}
                          style={{ padding: 0, background: "none", border: "none" }}
                        >
                          <FaDownload />
                        </Button>
                      )}
                    </td>
                    <td className="px-2 py-1 font-mono">{row?.[1] ?? ""}</td>
                  </tr>
                ))}
                {!rdeGraphs?.length && (
                  <tr><td className="px-2 py-3 text-gray-500" colSpan={2}>No data</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
      {toast && <Pill>{toast}</Pill>}
    </Section>
  );
}
