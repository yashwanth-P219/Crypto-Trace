import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertOctagon, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
  onReset?: () => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({ errorInfo });
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 my-4 bg-white border border-red-200 rounded-2xl text-slate-700 shadow-sm max-w-4xl mx-auto">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-red-600 shrink-0">
              <AlertOctagon className="w-8 h-8" />
            </div>
            <div className="space-y-2 flex-1">
              <h2 className="text-lg font-bold text-[#1E293B]">
                {this.props.fallbackTitle || 'Forensic Component Render Error'}
              </h2>
              <p className="text-sm text-slate-600">
                An unexpected runtime error occurred while displaying this section. The application remains running.
              </p>
              
              {this.state.error && (
                <div className="p-3 bg-red-50/50 border border-red-200 rounded-lg text-xs font-mono text-red-700 overflow-x-auto">
                  <strong>Error:</strong> {this.state.error.toString()}
                </div>
              )}

              <div className="pt-3 flex items-center gap-3">
                <button
                  type="button"
                  onClick={this.handleReset}
                  className="px-4 py-2 bg-[#2563EB] hover:bg-blue-700 text-white rounded-xl text-xs font-semibold flex items-center gap-2 transition-all shadow-sm cursor-pointer"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  Try Again
                </button>
                <button
                  type="button"
                  onClick={() => window.location.reload()}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 rounded-xl text-xs font-medium transition-all cursor-pointer"
                >
                  Reload Page
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
