import React from "react";


// =====================
// Config
// =====================
// Set the API base URL. If your backend follows the cli.py env, it is usually
// http://<PROVSTOR_API_ENDPOINT_HOST>:<PROVSTOR_API_ENDPOINT_PORT>
// You can override this at runtime from the UI as well.

// Helper: fetch wrapper with JSON + errors
export async function fetchJSON(input: RequestInfo, init?: RequestInit) {
  const res = await fetch(input, init);
  console.log("fetch", input, res.status);
  const contentType = res.headers.get("content-type") || "";
  if (!res.ok) {
    let detail: any = await (contentType.includes("application/json") ? res.json().catch(() => ({})) : res.text());
    throw new Error(typeof detail === "string" ? detail : detail?.detail || `HTTP ${res.status}`);
  }
  if (contentType.includes("application/json")) return res.json();
  return res.text();
}

// File download helper
export async function downloadGET(url: string, filenameHint?: string) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Download failed: HTTP ${res.status}`);
  const blob = await res.blob();
  const cd = res.headers.get("Content-Disposition");
  const nameFromHeader = cd && /filename="?([^";]+)"?/i.exec(cd)?.[1];
  const filename = nameFromHeader || filenameHint || "download";
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(a.href);
}

// Small UI helpers
export function Section({ title, children, right }: { title: string; children: React.ReactNode; right?: React.ReactNode }) {
  return (
    <div className="bg-white rounded-2xl shadow p-5 space-y-4 border border-gray-100">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">{title}</h2>
        {right}
      </div>
      {children}
    </div>
  );
}

export function Pill({ children }: { children: React.ReactNode }) {
  return <span className="px-2 py-0.5 rounded-full text-xs bg-gray-100">{children}</span>;
}

export function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="grid grid-cols-12 gap-3 items-start">
      <div className="col-span-12 md:col-span-3 text-sm font-medium pt-2">{label}</div>
      <div className="col-span-12 md:col-span-9">{children}</div>
    </label>
  );
}

export function Button(props: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      className={("px-3 py-2 rounded-xl text-sm border shadow-sm hover:shadow transition disabled:opacity-50 disabled:cursor-not-allowed " +
        (props.className || ""))}
    />
  );
}

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(function Input(props, ref) {
  return <input ref={ref} {...props} className={("w-full px-3 py-2 rounded-xl border focus:outline-none focus:ring-2 focus:ring-gray-200 " + (props.className || ""))} />;
});

export function Textarea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea {...props} className={("w-full px-3 py-2 rounded-xl border min-h-[140px] font-mono text-sm focus:outline-none focus:ring-2 focus:ring-gray-200 " + (props.className || ""))} />;
}

export function Tabs<T extends string>({ value, onChange, tabs }: { value: T; onChange: (v: T) => void; tabs: { value: T; label: string }[] }) {
  return (
    <div className="flex flex-wrap gap-2">
      {tabs.map((t) => (
        <Button
          key={String(t.value)}
          onClick={() => onChange(t.value)}
        >
          <p
            className={" " + (value === t.value ? "font-bold text-black" : "text-gray-800")}
          >
            {t.label}
          </p>
        </Button>
      ))}
    </div>
  );
}