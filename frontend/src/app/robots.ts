import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: ["/admin", "/api/", "/auth/", "/account"],
      },
    ],
    sitemap: "https://www.benimmasalim.com.tr/sitemap.xml",
  };
}
