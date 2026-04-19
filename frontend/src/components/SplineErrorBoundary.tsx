// @ts-nocheck
import React, { Component, ReactNode } from 'react';

interface Props {
  children?: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
}

export class SplineErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  public static getDerivedStateFromError(_: Error): State {
    return { hasError: true };
  }

  public componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('SplineErrorBoundary caught an error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="w-full h-full flex items-center justify-center bg-black text-[#555] font-mono text-[10px] uppercase tracking-widest relative z-0 pointer-events-none p-10 text-center border-dashed border-2 border-[#333]">
          <div className="flex flex-col gap-2 relative">
            <span className="text-[12px] font-black text-red-500">[ DATALINK ERROR ]</span>
            <span>External 3D Asset Failed to Initialize</span>
            <span className="opacity-50 mt-4 leading-relaxed">Ensure CORS and physics/WASM requirements are met, or network blocks are disabled.</span>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
