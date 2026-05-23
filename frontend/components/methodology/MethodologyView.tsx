"use client";

import { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { fetchMethodology } from "@/lib/api";

export default function MethodologyView() {
  const [lang, setLang] = useState<"zh" | "en">("zh");
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(true);
  const [expandAll, setExpandAll] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetchMethodology(lang)
      .then((c) => setContent(c))
      .finally(() => setLoading(false));
  }, [lang]);

  // Parse sections (## headers)
  const sections = content.split(/\n(?=## )/).filter(Boolean);

  return (
    <div className="space-y-4">
      {/* Language toggle */}
      <div className="flex items-center gap-4">
        <span className="text-sm text-gray-400">Language / 语言:</span>
        <div className="flex rounded-lg overflow-hidden border border-border">
          <button
            onClick={() => setLang("zh")}
            className={`px-4 py-1.5 text-sm transition-colors ${
              lang === "zh" ? "bg-accent text-white" : "bg-surface text-gray-400 hover:text-white"
            }`}
          >
            中文
          </button>
          <button
            onClick={() => setLang("en")}
            className={`px-4 py-1.5 text-sm transition-colors ${
              lang === "en" ? "bg-accent text-white" : "bg-surface text-gray-400 hover:text-white"
            }`}
          >
            English
          </button>
        </div>
        <label className="flex items-center gap-2 text-sm text-gray-400 ml-auto">
          <input
            type="checkbox"
            checked={expandAll}
            onChange={(e) => setExpandAll(e.target.checked)}
            className="accent-accent"
          />
          Expand All / 全部展开
        </label>
      </div>

      {loading ? (
        <div className="text-gray-400 py-12 text-center">Loading...</div>
      ) : (
        <div className="space-y-3">
          {sections.map((section, idx) => {
            // Extract title from ## header
            const lines = section.trim().split("\n");
            const titleLine = lines[0];
            const title = titleLine.replace(/^## /, "");
            const body = lines.slice(1).join("\n");

            // Sections 0-1 expanded by default
            const defaultOpen = idx < 2;

            return (
              <details key={idx} className="card" open={expandAll || defaultOpen}>
                <summary className="cursor-pointer text-base font-medium text-white hover:text-accent transition-colors">
                  {title}
                </summary>
                <div className="mt-4 prose prose-invert max-w-none text-sm text-gray-300 leading-relaxed">
                  <ReactMarkdown
                    remarkPlugins={[remarkMath]}
                    rehypePlugins={[rehypeKatex]}
                    components={{
                      // Render LaTeX inline
                      p: ({ children }) => <p className="mb-3">{children}</p>,
                      // Render raw LaTeX blocks
                      code: ({ className, children, ...props }) => {
                        const match = /language-(\w+)/.exec(className || "");
                        if (match) {
                          return <code className={className} {...props}>{children}</code>;
                        }
                        return <code className="bg-surface px-1 py-0.5 rounded text-accent">{children}</code>;
                      },
                    }}
                  >
                    {body}
                  </ReactMarkdown>
                </div>
              </details>
            );
          })}
        </div>
      )}

      {/* Footer */}
      <hr className="border-border" />
      <p className="text-xs text-gray-500">
        This methodology is maintained as a living document. Last updated: 2026-05-23.
      </p>
    </div>
  );
}
