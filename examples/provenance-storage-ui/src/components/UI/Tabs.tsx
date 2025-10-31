import { Button } from "./Button";

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
