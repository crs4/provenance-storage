// API logic for ProvStorUI
// Contains endpoint construction and fetch helpers

export function buildApiEndpoints(baseUrl: string) {
  const root = baseUrl.replace(/\/$/, "");
  const join = (p: string) => root + p;
  return {
    status: join("/status/"),
    uploadCrate: join("/upload/crate/"),
    runQuery: join("/query/run-query/"),
    listGraphs: join("/query/list-graphs/"),
    listRDEGraphs: join("/query/list-RDE-graphs/"),
    getCrate: join("/get/crate/"),
    getFile: join("/get/file/"),
    getGraphsForFile: join("/get/graphs-for-file/"),
    getGraphsForResult: join("/get/graphs-for-result/"),
    getWorkflow: join("/get/workflow/"),
    getRunResults: join("/get/run-results/"),
    getRunObjects: join("/get/run-objects/"),
    getObjectsForResult: join("/get/objects-for-result/"),
    getActionsForResult: join("/get/actions-for-result/"),
    getObjectsForAction: join("/get/objects-for-action/"),
    getResultsForAction: join("/get/results-for-action/"),
    getRunParams: join("/get/run-params/"),
  };
}

export async function fetchJSON(input: RequestInfo, init?: RequestInit) {
  const res = await fetch(input, init);
  const contentType = res.headers.get("content-type") || "";
  if (!res.ok) {
    let detail: any = await (contentType.includes("application/json") ? res.json().catch(() => ({})) : res.text());
    throw new Error(typeof detail === "string" ? detail : detail?.detail || `HTTP ${res.status}`);
  }
  if (contentType.includes("application/json")) return res.json();
  return res.text();
}

export async function downloadGET(url: string, filenameHint?: string) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Download failed: HTTP ${res.status}`);
  const blob = await res.blob();
  const cd = res.headers.get("Content-Disposition");

  let filename: string | undefined;
  if (cd) {
    const match = /filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/i.exec(cd);
    if (match) {
      filename = decodeURIComponent(match[1] || match[2]);
    }
  }
  if (!filename && filenameHint) {
    const parts = filenameHint.split("/");
    filename = parts[parts.length - 1] || undefined;
  }
  // Fallback
  if (!filename) filename = "downloaded_file";

  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(a.href);
}
