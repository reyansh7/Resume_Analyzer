"use client";

import Image from "next/image";
import { UploadCloud, X } from "lucide-react";
import { cn } from "@/lib/utils";
import pdfPreview from "@/app/pdf.png";

type UploadZoneProps = {
  dragging: boolean;
  selectedFile: File | null;
  onSelectFile: (file: File) => void;
  onClearFile: () => void;
  setDragging: (value: boolean) => void;
};

export function UploadZone({ dragging, selectedFile, onSelectFile, onClearFile, setDragging }: UploadZoneProps) {
  const hasPdf = Boolean(selectedFile && selectedFile.type === "application/pdf");

  return (
    <label
      className={cn(
        "relative flex min-h-64 cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed border-primary/35 bg-white/60 p-8 text-center transition-all duration-300 dark:bg-white/5",
        dragging && "scale-[1.01] border-primary shadow-soft"
      )}
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        const file = e.dataTransfer.files?.[0];
        setDragging(false);
        if (file) onSelectFile(file);
      }}
    >
      <div className="absolute inset-0 rounded-2xl bg-secondary/20 opacity-90" />
      {hasPdf ? (
        <>
          <button
            type="button"
            aria-label="Clear selected PDF"
            className="absolute right-3 top-3 z-10 inline-flex h-7 w-7 items-center justify-center rounded-full border border-primary/50 bg-primary/10 text-sm font-bold text-primary transition hover:bg-primary/20"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              onClearFile();
            }}
          >
            <X className="h-3.5 w-3.5" />
          </button>
          <div className="relative h-20 w-20 overflow-hidden rounded-xl border border-primary/25 bg-white/80 p-1 shadow-sm dark:bg-white/10">
            <Image src={pdfPreview} alt="PDF uploaded" className="h-full w-full object-contain" priority />
          </div>
          <p className="relative text-lg font-semibold text-primary">PDF Selected</p>
          <p className="relative max-w-[90%] truncate text-sm text-muted-foreground">{selectedFile?.name}</p>
          <p className="relative text-xs text-muted-foreground">Drop another PDF or click to replace</p>
        </>
      ) : (
        <>
          <UploadCloud className="relative h-10 w-10 text-primary" />
          <p className="relative text-lg font-medium">Drop your resume PDF here</p>
          <p className="relative text-sm text-muted-foreground">or click to browse your file</p>
        </>
      )}
      <input
        type="file"
        accept="application/pdf"
        className="sr-only"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) onSelectFile(file);
        }}
      />
    </label>
  );
}
