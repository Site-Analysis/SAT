// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { useState, type ReactNode } from "react";
import { ChevronDown } from "lucide-react";
import { C, hairline, sectionLabel } from "./theme";

interface CollapsibleSubsectionProps {
  title: string;
  defaultOpen?: boolean;
  footnote?: ReactNode;
  children: ReactNode;
}

export function CollapsibleSubsection({
  title,
  defaultOpen = false,
  footnote,
  children,
}: CollapsibleSubsectionProps) {
  const [open, setOpen] = useState(defaultOpen);
  const id = `contour-sub-${title.replace(/\s+/g, "-").toLowerCase()}`;

  return (
    <div style={{ borderTop: hairline, paddingTop: 10 }}>
      <button
        type="button"
        aria-expanded={open}
        aria-controls={id}
        onClick={() => setOpen((v) => !v)}
        className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-secondary"
        style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          width: "100%",
          background: "none",
          border: "none",
          padding: 0,
          cursor: "pointer",
          textAlign: "left",
        }}
      >
        <span style={{ ...sectionLabel, flex: 1 }}>{title}</span>
        <ChevronDown
          size={12}
          color={C.inkSoft}
          aria-hidden
          className="motion-safe:transition-transform motion-safe:duration-200"
          style={{ transform: open ? "rotate(180deg)" : "rotate(0deg)" }}
        />
      </button>
      {footnote ? <div style={{ marginTop: 6 }}>{footnote}</div> : null}
      <div
        id={id}
        className="grid motion-safe:transition-[grid-template-rows] motion-safe:duration-200 motion-safe:ease-in-out"
        style={{ gridTemplateRows: open ? "1fr" : "0fr" }}
      >
        <div style={{ overflow: "hidden" }}>
          <div style={{ paddingTop: 10 }}>{children}</div>
        </div>
      </div>
    </div>
  );
}
