// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { useId, useState } from "react";
import { C } from "./theme";

interface InfoTipProps {
  label: string;
  text: string;
}

export function InfoTip({ label, text }: InfoTipProps) {
  const uid = useId();
  const tipId = `${uid}-tip`;
  const [hover, setHover] = useState(false);
  const [pinned, setPinned] = useState(false);
  const open = hover || pinned;

  function close() {
    setHover(false);
    setPinned(false);
  }

  return (
    <span style={{ position: "relative", display: "inline-flex", verticalAlign: "middle" }}>
      <button
        type="button"
        aria-label={`${label} help`}
        aria-describedby={open ? tipId : undefined}
        aria-expanded={open}
        onMouseEnter={() => setHover(true)}
        onMouseLeave={() => setHover(false)}
        onFocus={() => setHover(true)}
        onBlur={close}
        onClick={(e) => {
          e.preventDefault();
          setPinned((v) => !v);
        }}
        onKeyDown={(e) => {
          if (e.key === "Escape") {
            e.stopPropagation();
            close();
            (e.currentTarget as HTMLButtonElement).blur();
          }
        }}
        className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-secondary"
        style={{
          width: 16,
          height: 16,
          borderRadius: 999,
          border: `1px solid ${C.border}`,
          background: C.surface,
          color: C.inkSoft,
          fontSize: 10,
          fontWeight: 700,
          lineHeight: 1,
          cursor: "help",
          padding: 0,
        }}
      >
        ?
      </button>
      {open ? (
        <span
          id={tipId}
          role="tooltip"
          style={{
            position: "absolute",
            zIndex: 20,
            left: 20,
            top: "50%",
            transform: "translateY(-50%)",
            width: 220,
            background: C.ink,
            color: C.surface,
            fontSize: 11,
            lineHeight: 1.45,
            fontWeight: 400,
            padding: "8px 10px",
            borderRadius: 8,
            boxShadow: "0 4px 18px rgba(0,0,0,0.18)",
          }}
        >
          {text}
        </span>
      ) : null}
    </span>
  );
}
