"use client";

import { createContext, useContext, useState, useCallback, ReactNode } from "react";

export type ToastType = "success" | "error" | "warning" | "info";

export interface Toast {
  id: string;
  message: string;
  type: ToastType;
}

interface ToastContextType {
  toasts: Toast[];
  toast: (message: string, type?: ToastType) => void;
  dismiss: (id: string) => void;
}

import { createContext as _createContext } from "react";

// We export the context so ToastProvider can consume it
export const ToastContext = createContext<ToastContextType>({
  toasts: [],
  toast: () => {},
  dismiss: () => {},
});

export function useToast() {
  return useContext(ToastContext);
}
