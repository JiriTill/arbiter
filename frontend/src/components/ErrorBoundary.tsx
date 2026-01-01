"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";
import { Button } from "@/components/ui/button";

interface Props {
    children: ReactNode;
    fallback?: ReactNode;
}

interface State {
    hasError: boolean;
    error?: Error;
    errorInfo?: ErrorInfo;
}

/**
 * Error Boundary component that catches React errors and displays a fallback UI.
 * 
 * Usage:
 * <ErrorBoundary>
 *   <YourComponent />
 * </ErrorBoundary>
 */
export class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        // Log error to console in development
        console.error("ErrorBoundary caught an error:", error, errorInfo);

        this.setState({ error, errorInfo });

        // In production, you would send this to an error tracking service
        // Example: Sentry.captureException(error, { extra: errorInfo });
    }

    handleReset = () => {
        this.setState({ hasError: false, error: undefined, errorInfo: undefined });
    };

    handleGoHome = () => {
        window.location.href = "/";
    };

    render() {
        if (this.state.hasError) {
            // Custom fallback if provided
            if (this.props.fallback) {
                return this.props.fallback;
            }

            // Default error UI
            return (
                <div className="flex min-h-[50vh] flex-col items-center justify-center p-6 text-center">
                    <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10">
                        <AlertTriangle className="h-8 w-8 text-destructive" />
                    </div>

                    <h2 className="mb-2 text-xl font-semibold text-foreground">
                        Something went wrong
                    </h2>

                    <p className="mb-6 max-w-md text-sm text-muted-foreground">
                        We encountered an unexpected error. This has been logged and we'll look into it.
                    </p>

                    {/* Error details in development */}
                    {process.env.NODE_ENV === "development" && this.state.error && (
                        <div className="mb-6 max-w-lg overflow-auto rounded-lg border border-border bg-card p-4 text-left">
                            <p className="mb-2 font-mono text-xs text-destructive">
                                {this.state.error.message}
                            </p>
                            {this.state.errorInfo && (
                                <pre className="text-xs text-muted-foreground overflow-x-auto">
                                    {this.state.errorInfo.componentStack}
                                </pre>
                            )}
                        </div>
                    )}

                    <div className="flex gap-3">
                        <Button
                            variant="outline"
                            onClick={this.handleReset}
                            className="gap-2"
                        >
                            <RefreshCw className="h-4 w-4" />
                            Try Again
                        </Button>

                        <Button
                            onClick={this.handleGoHome}
                            className="gap-2"
                        >
                            <Home className="h-4 w-4" />
                            Go Home
                        </Button>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

/**
 * Higher-order component to wrap any component with error boundary.
 */
export function withErrorBoundary<P extends object>(
    WrappedComponent: React.ComponentType<P>,
    fallback?: ReactNode
) {
    return function WithErrorBoundary(props: P) {
        return (
            <ErrorBoundary fallback={fallback}>
                <WrappedComponent {...props} />
            </ErrorBoundary>
        );
    };
}
