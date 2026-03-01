/**
 * Shared admin authentication helpers.
 *
 * All admin pages and API modules should import from here instead of
 * defining their own inline getAuthHeaders() closures.
 */

export { API_BASE_URL } from "@/lib/api";

/** JSON request headers with Bearer token. */
export function getAdminHeaders(): HeadersInit {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") : null;
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token ?? ""}`,
  };
}

/** Non-JSON request headers (file upload, blob download, etc.) with Bearer token. */
export function getAdminHeadersNoContent(): HeadersInit {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") : null;
  return {
    Authorization: `Bearer ${token ?? ""}`,
  };
}
