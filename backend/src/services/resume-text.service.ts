import pdfParse from "pdf-parse";

const DEFAULT_QUALITY_THRESHOLD = 0.62;

type ExtractedTextCandidate = {
  source: "pdf-parse" | "pdfjs";
  text: string;
  quality: number;
};

function normalizeExtractedText(raw: string): string {
  let text = raw || "";
  text = text.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  text = text.replace(/\u00a0/g, " ");
  text = text.replace(/[\u2022\u2023\u25E6\u2043\u2219■▪●□▣◆◇◦]/g, "\n- ");
  text = text.replace(/\t/g, " ");
  text = text.replace(/[ \f\v]+/g, " ");
  text = text.replace(/\n{3,}/g, "\n\n");
  return text.trim();
}

function scoreTextQuality(text: string): number {
  const normalized = text.trim();
  if (!normalized) return 0;

  const tokens = normalized.split(/\s+/).filter(Boolean);
  if (!tokens.length) return 0;

  const minLenScore = Math.min(1, normalized.length / 1200);

  const longTokenCount = tokens.filter((token) => token.length >= 22).length;
  const longTokenPenalty = Math.min(1, longTokenCount / Math.max(1, tokens.length * 0.08));

  const suspiciousFragmentCount = (normalized.match(/\b[A-Za-z]{2,}\s[A-Za-z]{1,3}\b/g) || []).length;
  const fragmentPenalty = Math.min(1, suspiciousFragmentCount / Math.max(1, tokens.length * 0.06));

  const alphaChars = (normalized.match(/[A-Za-z]/g) || []).length;
  const vowelChars = (normalized.match(/[AEIOUaeiou]/g) || []).length;
  const vowelRatio = alphaChars > 0 ? vowelChars / alphaChars : 0;
  const vowelScore = Math.max(0, Math.min(1, (vowelRatio - 0.18) / 0.18));

  const separators = (normalized.match(/[.\n:;,\-|]/g) || []).length;
  const structureScore = Math.min(1, separators / Math.max(12, tokens.length * 0.06));

  const quality =
    0.34 * minLenScore +
    0.26 * vowelScore +
    0.22 * structureScore +
    0.18 * (1 - longTokenPenalty) -
    0.24 * fragmentPenalty;

  return Math.max(0, Math.min(1, quality));
}

async function extractWithPdfParse(fileBuffer: Buffer): Promise<ExtractedTextCandidate> {
  const parsed = await pdfParse(fileBuffer);
  const text = normalizeExtractedText(parsed.text || "");
  return {
    source: "pdf-parse",
    text,
    quality: scoreTextQuality(text)
  };
}

async function extractWithPdfJs(fileBuffer: Buffer): Promise<ExtractedTextCandidate> {
  const pdfjs = await import("pdfjs-dist/legacy/build/pdf.mjs");

  const loadingTask = pdfjs.getDocument({ data: new Uint8Array(fileBuffer) });
  const document = await loadingTask.promise;
  const pageCount = Math.min(document.numPages, 8);

  const pageTexts: string[] = [];

  for (let pageIndex = 1; pageIndex <= pageCount; pageIndex++) {
    const page = await document.getPage(pageIndex);
    const content = await page.getTextContent();

    const items = (content.items as Array<{ str?: string; transform?: number[] }>).filter((item) => item.str && item.str.trim());

    const lineBuckets = new Map<number, Array<{ x: number; value: string }>>();

    for (const item of items) {
      const transform = Array.isArray(item.transform) ? item.transform : [0, 0, 0, 0, 0, 0];
      const y = Math.round((transform[5] ?? 0) / 2) * 2;
      const x = transform[4] ?? 0;
      const value = (item.str || "").trim();
      if (!value) continue;

      const existing = lineBuckets.get(y) || [];
      existing.push({ x, value });
      lineBuckets.set(y, existing);
    }

    const lineKeys = [...lineBuckets.keys()].sort((a, b) => b - a);
    const lines: string[] = [];

    for (const key of lineKeys) {
      const sorted = (lineBuckets.get(key) || []).sort((a, b) => a.x - b.x);
      const mergedLine = sorted
        .map((entry) => entry.value)
        .join(" ")
        .replace(/\s+/g, " ")
        .trim();

      if (mergedLine) lines.push(mergedLine);
    }

    pageTexts.push(lines.join("\n"));
  }

  const text = normalizeExtractedText(pageTexts.join("\n\n"));
  return {
    source: "pdfjs",
    text,
    quality: scoreTextQuality(text)
  };
}

export async function extractResumeText(fileBuffer: Buffer): Promise<{ text: string; source: "pdf-parse" | "pdfjs"; quality: number }> {
  const primary = await extractWithPdfParse(fileBuffer);

  if (primary.quality >= DEFAULT_QUALITY_THRESHOLD || primary.text.length >= 2500) {
    return primary;
  }

  try {
    const fallback = await extractWithPdfJs(fileBuffer);

    if (fallback.quality > primary.quality + 0.05 || fallback.text.length > primary.text.length * 1.15) {
      return fallback;
    }
  } catch {
    // ignore fallback errors and keep primary result
  }

  return primary;
}
