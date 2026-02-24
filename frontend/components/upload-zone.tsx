"use client";

import { UploadCloud } from "lucide-react";
import { cn } from "@/lib/utils";

type UploadZoneProps = {
  dragging: boolean;
  onSelectFile: (file: File) => void;
  setDragging: (value: boolean) => void;
};

export function UploadZone({ dragging, onSelectFile, setDragging }: UploadZoneProps) {
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
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-indigo-400/15 via-cyan-300/15 to-violet-300/15 opacity-80" />
      <UploadCloud className="relative h-10 w-10 text-primary" />
      <p className="relative text-lg font-medium">Drop your resume PDF here</p>
      <p className="relative text-sm text-muted-foreground">or click to browse your file</p>
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
