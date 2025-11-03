import React from "react";

export function Button(props: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      className={("px-3 py-2 rounded-xl text-sm border shadow-sm hover:shadow transition disabled:opacity-50 disabled:cursor-not-allowed " +
        (props.className || ""))}
    />
  );
}
