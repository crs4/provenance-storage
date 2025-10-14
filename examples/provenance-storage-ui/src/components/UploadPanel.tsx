import { useRef, useState } from "react";
import { Section } from "./UI/Section";
import { Row } from "./UI/Row";
import { Button } from "./UI/Button";
import { Input } from "./UI/Input";
import { Pill } from "./UI/Pill";
import { AiOutlineLoading3Quarters } from "react-icons/ai";



interface UploadPanelProps {
  api: ReturnType<typeof import("../utils/api").buildApiEndpoints>;
  setBusy: (b: boolean) => void;
  toast: string | null;
  setToast: (t: string | null) => void;
}

export function UploadPanel({ api, setBusy, toast, setToast }: UploadPanelProps) {
  const fileRef = useRef<HTMLInputElement | null>(null);
  const [uploadInfo, setUploadInfo] = useState<{ crate_url?: string; result?: string } | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  async function uploadCrate() {
    const file = fileRef.current?.files?.[0];
    if (!file) return setToast("Pick a ZIP first");
    setBusy(true);
    setIsUploading(true);
    setUploadInfo(null); // Clear previous results
    try {
      const fd = new FormData();
      fd.append("crate_path", file, file.name);
      const res = await fetch(api.uploadCrate, { method: "POST", body: fd });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setUploadInfo(json);
      setToast("Uploaded");
    } catch (e: any) {
      setUploadInfo(null);
      setToast("Upload failed: " + e.message);
    } finally {
      setBusy(false);
      setIsUploading(false);
    }
  }

  return (
    <Section title="Upload Crate">
      <Row label="RO-Crate (.zip)">
        <Input type="file" accept=".zip" ref={fileRef} />
      </Row>
      <Button onClick={uploadCrate}>POST /upload/crate/</Button>
      
      {isUploading && (
        <div className="flex items-center gap-2">
          <AiOutlineLoading3Quarters className="animate-spin" size={16} />
          <span className="text-sm">Uploading...</span>
        </div>
      )}
      
      {uploadInfo && !isUploading && (
        <div className="text-sm">
          <div>Result: <Pill>{uploadInfo.result}</Pill></div>
          {uploadInfo.crate_url && (
            <div className="truncate">Crate URL: <a href={uploadInfo.crate_url} className="underline" target="_blank" rel="noreferrer">{uploadInfo.crate_url}</a></div>
          )}
        </div>
      )}
      {toast && <Pill>{toast}</Pill>}
    </Section>
  );
}
