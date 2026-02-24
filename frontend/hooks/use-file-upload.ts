"use client";

import type React from "react";
import { useState } from "react";

export function useFileUpload() {
  const [dragging, setDragging] = useState(false);

  return {
    dragging,
    setDragging,
    dragHandlers: {
      onDragOver: (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        setDragging(true);
      },
      onDragLeave: () => setDragging(false),
      onDrop: (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        setDragging(false);
      }
    }
  };
}
