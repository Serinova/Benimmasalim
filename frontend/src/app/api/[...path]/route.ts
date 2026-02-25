/**
 * Catch-all API proxy route handler.
 *
 * Replaces Next.js rewrites() proxy for /api/* requests.
 * Reason: rewrites proxy has a ~30s default timeout which is too short
 * for AI story generation (can take 60-90 seconds for 32-page stories).
 *
 * Security:
 * - Blocks direct proxy access to admin/internal paths
 * - Sanitizes error messages (no internal details leaked)
 * - Only forwards safe headers
 */

const BACKEND_URL =
  process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:8000";

const PROXY_TIMEOUT_MS = 180_000;

// Sadece internal (servisler arası) path'ler proxy'den engellenir.
// v1/admin backend'de JWT + AdminUser ile korunuyor; proxy geçişine izin verilir.
const BLOCKED_PATH_PREFIXES = ["v1/internal"];

const JSON_HEADERS = { "Content-Type": "application/json" } as const;

function forbidden(msg: string): Response {
  return new Response(JSON.stringify({ detail: msg }), {
    status: 403,
    headers: JSON_HEADERS,
  });
}

async function proxyRequest(
  request: Request,
  { params }: { params: { path: string[] } },
): Promise<Response> {
  const path = params.path.join("/");

  const lowerPath = path.toLowerCase();
  if (BLOCKED_PATH_PREFIXES.some((p) => lowerPath.startsWith(p))) {
    return forbidden("Bu endpoint proxy üzerinden erişilemez");
  }

  const targetUrl = `${BACKEND_URL}/api/${path}`;

  const url = new URL(request.url);
  const qs = url.search;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), PROXY_TIMEOUT_MS);

  try {
    const headers = new Headers();
    const fwdHeaders = [
      "content-type",
      "authorization",
      "accept",
      "accept-language",
      "x-request-id",
      "x-trial-token",
    ];
    for (const h of fwdHeaders) {
      const v = request.headers.get(h);
      if (v) headers.set(h, v);
    }

    // Forward only the first client IP (prevent chain spoofing)
    const rawIp =
      request.headers.get("x-forwarded-for") ||
      request.headers.get("x-real-ip");
    if (rawIp) {
      const firstIp = rawIp.split(",")[0].trim();
      headers.set("x-forwarded-for", firstIp);
    }

    const fetchOptions: RequestInit = {
      method: request.method,
      headers,
      signal: controller.signal,
    };

    if (request.method !== "GET" && request.method !== "HEAD") {
      fetchOptions.body = Buffer.from(await request.arrayBuffer());
    }

    const backendResponse = await fetch(`${targetUrl}${qs}`, fetchOptions);

    const responseHeaders = new Headers();
    const passHeaders = [
      "content-type",
      "content-disposition",
      "cache-control",
      "x-request-id",
    ];
    for (const h of passHeaders) {
      const v = backendResponse.headers.get(h);
      if (v) responseHeaders.set(h, v);
    }

    return new Response(backendResponse.body, {
      status: backendResponse.status,
      statusText: backendResponse.statusText,
      headers: responseHeaders,
    });
  } catch (error: unknown) {
    if (error instanceof Error && error.name === "AbortError") {
      return new Response(
        JSON.stringify({
          detail: "İstek zaman aşımına uğradı. Lütfen tekrar deneyin.",
        }),
        { status: 504, headers: JSON_HEADERS },
      );
    }

    // Never expose internal error details (hostnames, ports, etc.)
    console.error("[API Proxy] Error:", error instanceof Error ? error.message : "unknown");
    return new Response(
      JSON.stringify({ detail: "Sunucu şu anda kullanılamıyor. Lütfen tekrar deneyin." }),
      { status: 502, headers: JSON_HEADERS },
    );
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function GET(
  request: Request,
  context: { params: { path: string[] } }
) {
  return proxyRequest(request, context);
}

export async function POST(
  request: Request,
  context: { params: { path: string[] } }
) {
  return proxyRequest(request, context);
}

export async function PUT(
  request: Request,
  context: { params: { path: string[] } }
) {
  return proxyRequest(request, context);
}

export async function PATCH(
  request: Request,
  context: { params: { path: string[] } }
) {
  return proxyRequest(request, context);
}

export async function DELETE(
  request: Request,
  context: { params: { path: string[] } }
) {
  return proxyRequest(request, context);
}
