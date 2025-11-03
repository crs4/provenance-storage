import React from "react";

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(function Input(props, ref) {
  return <input ref={ref} {...props} className={("w-full px-3 py-2 rounded-xl border focus:outline-none focus:ring-2 focus:ring-gray-200 " + (props.className || ""))} />;
});
