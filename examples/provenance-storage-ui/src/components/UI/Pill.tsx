import React from "react";

export function Pill({ children }: { children: React.ReactNode }) {
  return <span className="px-2 py-0.5 rounded-full text-xs bg-gray-100">{children}</span>;
}
