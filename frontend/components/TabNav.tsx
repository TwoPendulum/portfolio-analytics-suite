"use client";

const TABS = [
  { id: "correlation", label: "Dynamic Correlation Tracking" },
  { id: "frontier", label: "Efficient Frontier" },
  { id: "methodology", label: "Methodology" },
];

interface TabNavProps {
  active: string;
  onChange: (id: string) => void;
}

export default function TabNav({ active, onChange }: TabNavProps) {
  return (
    <div className="flex space-x-1 border-b border-border/50">
      {TABS.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
            active === tab.id
              ? "border-accent text-accent"
              : "border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-600"
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
