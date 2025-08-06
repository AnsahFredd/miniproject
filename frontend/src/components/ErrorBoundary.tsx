import React, {Component, ErrorInfo, ReactNode} from 'react'
import {analytics} from "../hooks/useAnalytics"

interface Props {
    children: ReactNode;
    fallback?: ReactNode;
    onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
    hasError: boolean;
    error?: Error
}

export class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false
    }

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error}
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.log("Route Error Boundary caught an errir", error, errorInfo)

        // Track error in analytics
        analytics.track('route_error', {
            error: error.message,
            stack: error.stack,
            componentStack: errorInfo.componentStack
        });

        // Call error handler if provided
        this.props.onError?.(error, errorInfo)

    }

    public render() {
        if (this.state.hasError) {
            return this.props.fallback || (
                <div className='min-h-screen flex items-center justify-center bg-gray-50'>
                    <div className='max-w-md w-full bg-white shadow-lg rounded-lg p-6'>
                        <div className='flex items-center justify-around w-12 h-12 mx-auto bg-red-100 rounded-full'>
                            <svg className='w-6 h-6 text-red-600' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                                <path strokeLinecap='round' strokeLinejoin='round' strokeWidth="2" d='M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'></path>
                            </svg>
                        </div>
                        <h3 className='mt-4 text-lg font-medium text-gray-900 text-center'>Something went wrong</h3>
                        <p className='mt-2 text-sm to-gray-500 text-center'>
                            We're sorry, but something unexpected happened. Pleae try refreshing the page
                        </p>
                        <button
                        onClick={() => window.location.reload()}
                        className='mt-4 w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors'
                        >
                            Refresh Page
                        </button>
                    </div>
                </div>
            )
        }
        return this.props.children
        
    }
}
