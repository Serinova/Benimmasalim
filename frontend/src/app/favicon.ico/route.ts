import { NextResponse } from "next/server";
import { readFile } from "node:fs/promises";
import path from "node:path";

export async function GET() {
  try {
    const filePath = path.join(process.cwd(), "public", "favicon.svg");
    const svg = await readFile(filePath, "utf-8");
    return new NextResponse(svg, {
      headers: { "Content-Type": "image/svg+xml" },
    });
  } catch {
    return new NextResponse(null, { status: 404 });
  }
}
