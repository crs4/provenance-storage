import React from "react";

export function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="grid grid-cols-12 gap-3 items-start">
      <div className="col-span-12 md:col-span-3 text-sm font-medium pt-2">{label}</div>
      <div className="col-span-12 md:col-span-9">{children}</div>
    </label>
  );
}
