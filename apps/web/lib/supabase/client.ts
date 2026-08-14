// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { createClient } from "@supabase/supabase-js";
import { getPublicEnv } from "@/lib/env";

const publicEnv = getPublicEnv();

// Single browser Supabase client — shared across pages so the auth session
// (including OAuth returns) persists in one place and is read back on load.
export const supabase = createClient(
  publicEnv.supabaseUrl,
  publicEnv.supabasePublishableKey,
  {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true, // parses ?code= on the OAuth callback
      flowType: "pkce",
    },
  },
);
