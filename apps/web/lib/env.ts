// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

type PublicEnv = {
  supabaseUrl: string;
  supabasePublishableKey: string;
};

// Next.js only inlines NEXT_PUBLIC_* when accessed as literal properties —
// dynamic process.env[name] stays undefined in the browser bundle.
function requirePublicEnvVar(
  name: string,
  value: string | undefined,
): string {
  if (!value) {
    throw new Error(
      `Missing required env var: ${name}. Set it in apps/web/.env.local.`,
    );
  }
  return value;
}

export function getPublicEnv(): PublicEnv {
  return {
    supabaseUrl: requirePublicEnvVar(
      "NEXT_PUBLIC_SUPABASE_URL",
      process.env.NEXT_PUBLIC_SUPABASE_URL,
    ),
    supabasePublishableKey: requirePublicEnvVar(
      "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY",
      process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY,
    ),
  };
}

export function requirePublicEnv(): void {
  getPublicEnv();
}
