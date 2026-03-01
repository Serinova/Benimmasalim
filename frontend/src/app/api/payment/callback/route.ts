import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

const BACKEND_URL =
  process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:8000";

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const MAX_TOKEN_LEN = 500;

function getBaseUrl(request: NextRequest): string {
  const forwarded = request.headers.get("x-forwarded-host");
  const proto = request.headers.get("x-forwarded-proto") || "https";
  if (forwarded) return `${proto}://${forwarded}`;

  const host = request.headers.get("host");
  if (host && !host.startsWith("0.0.0.0") && !host.startsWith("127.0.0.1"))
    return `${proto}://${host}`;

  return process.env.NEXTAUTH_URL || request.url;
}

/**
 * Iyzico redirects the user here after checkout form submission.
 *
 * Supports two flows:
 * - ?orderId=UUID  → authenticated order flow (verify via /payments/verify-iyzico)
 * - ?trialId=UUID  → trial flow (pass token back to /create page for client-side verify)
 */
export async function POST(request: NextRequest) {
  const base = getBaseUrl(request);
  const errorUrl = (reason: string) =>
    new URL(`/create-v2?payment=error&reason=${reason}`, base);

  try {
    const formData = await request.formData();
    const token = (formData.get("token") as string | null)?.slice(0, MAX_TOKEN_LEN);
    const orderId = request.nextUrl.searchParams.get("orderId");
    const trialId = request.nextUrl.searchParams.get("trialId");

    if (!token) {
      return NextResponse.redirect(errorUrl("missing_token"));
    }

    // ── Trial flow: redirect back to /create with token for client-side verification ──
    if (trialId) {
      if (!UUID_RE.test(trialId)) {
        return NextResponse.redirect(errorUrl("invalid_trial"));
      }
      const encodedToken = encodeURIComponent(token);
      const trialToken = request.nextUrl.searchParams.get("tt") || "";
      const ttParam = trialToken ? `&tt=${encodeURIComponent(trialToken)}` : "";
      return NextResponse.redirect(
        new URL(`/create-v2?payment=success&trialId=${trialId}&token=${encodedToken}${ttParam}`, base),
      );
    }

    // ── Order flow: verify server-side via /payments/verify-iyzico ──
    if (!orderId) {
      return NextResponse.redirect(errorUrl("missing_token"));
    }

    if (!UUID_RE.test(orderId)) {
      return NextResponse.redirect(errorUrl("invalid_order"));
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15_000);

    try {
      const verifyRes = await fetch(
        `${BACKEND_URL}/api/v1/payments/verify-iyzico`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token, order_id: orderId }),
          signal: controller.signal,
        },
      );

      if (verifyRes.ok) {
        const data = await verifyRes.json();
        if (data.status === "success") {
          return NextResponse.redirect(
            new URL(`/create-v2?payment=success&orderId=${orderId}`, base),
          );
        }
      }
    } finally {
      clearTimeout(timeout);
    }

    return NextResponse.redirect(
      new URL(`/create-v2?payment=failed&orderId=${orderId}`, base),
    );
  } catch {
    return NextResponse.redirect(
      new URL(`/create-v2?payment=error&reason=server_error`, base),
    );
  }
}
