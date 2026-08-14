// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

type PublicEnv = {
  supabaseUrl: string;
  supabasePublishableKey: string;
};

const DEV_FALLBACKS: Record<string, string> = {
  NEXT_PUBLIC_SUPABASE_URL: "http://localhost:54321",
  NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY: "local-dev-placeholder",
};

function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    if (process.env.NODE_ENV !== "production" && DEV_FALLBACKS[name]) {
      console.warn(`Missing ${name}; using local development placeholder.`);
      return DEV_FALLBACKS[name];
    }
    throw new Error(
      `Missing required env var: ${name}. Copy .env.example to .env and set it.`
    );
  }
  return value;
}

export function getPublicEnv(): PublicEnv {
  return {
    supabaseUrl: requireEnv("NEXT_PUBLIC_SUPABASE_URL"),
    supabasePublishableKey: requireEnv(
      "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY"
    ),
  };
}

export function requirePublicEnv(): void {
  getPublicEnv();
}
