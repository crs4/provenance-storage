import React from "react";

export function Textarea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea {...props} className={("w-full px-3 py-2 rounded-xl border min-h-[140px] font-mono text-sm focus:outline-none focus:ring-2 focus:ring-gray-200 " + (props.className || ""))} />;
}
