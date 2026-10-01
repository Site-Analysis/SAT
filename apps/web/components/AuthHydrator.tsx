// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase/client";
import { useAuthStore } from "@/lib/stores/auth";
import type { User, Session } from "@supabase/supabase-js";

// Local-dev only: NEXT_PUBLIC_DEV_BYPASS_AUTH=1 skips Supabase and signs in a stub user.
// Inlined at build time — never set it in a deployed environment.
const DEV_BYPASS = process.env.NEXT_PUBLIC_DEV_BYPASS_AUTH === "1";
const DEV_USER = {
  id: "dev", email: "dev@local", aud: "authenticated", app_metadata: {},
  user_metadata: { full_name: "Dev User" }, created_at: "",
} as User;

// Reads the persisted Supabase session (incl. OAuth returns) back into the
// in-memory auth store before any page renders, and keeps it in sync. Gating
// render until the first session read avoids login-guard redirect flicker.
export function AuthHydrator({ children }: { children: React.ReactNode }) {
  const [ready, setReady] = useState(false);
  const setAuth   = useAuthStore((s) => s.setAuth);
  const clearAuth = useAuthStore((s) => s.clearAuth);

  useEffect(() => {
    if (DEV_BYPASS) {
      setAuth(DEV_USER, { access_token: "dev", user: DEV_USER } as unknown as Session);
      setReady(true);
      return;
    }
    let alive = true;

    supabase.auth.getSession().then(({ data }) => {
      if (!alive) return;
      if (data.session?.user) setAuth(data.session.user, data.session);
      setReady(true);
    });

    const { data: sub } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session?.user) setAuth(session.user, session);
      else clearAuth();
    });

    return () => { alive = false; sub.subscription.unsubscribe(); };
  }, [setAuth, clearAuth]);

  if (!ready) return null;
  return <>{children}</>;
}
