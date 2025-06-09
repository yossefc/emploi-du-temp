import React, { Component, ErrorInfo as ReactErrorInfo, ReactNode } from 'react';

// Types for error handling
export interface AppErrorInfo {
  message: string;
  stack?: string;
  component?: string;
  errorBoundary?: boolean;
  timestamp: Date;
  userAgent?: string;
  url?: string;
  userId?: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  category: 'network' | 'validation' | 'permission' | 'system' | 'user' | 'unknown';
  context?: Record<string, any>;
  retry?: () => void;
  recoveryActions?: Array<{
    label: string;
    action: () => void;
  }>;
}

export interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: AppErrorInfo | null;
}

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: (error: AppErrorInfo) => ReactNode;
  onError?: (error: AppErrorInfo) => void;
  enableReporting?: boolean;
  showDetails?: boolean;
  className?: string;
}

// Error boundary component
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private retryCount = 0;
  private maxRetries = 3;

  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, reactErrorInfo: ReactErrorInfo) {
    const errorInfo: AppErrorInfo = {
      message: error.message,
      stack: error.stack,
      component: reactErrorInfo.componentStack || undefined,
      errorBoundary: true,
      timestamp: new Date(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      severity: this.categorizeErrorSeverity(error),
      category: this.categorizeErrorType(error),
      context: {
        retryCount: this.retryCount,
        maxRetries: this.maxRetries,
        reactErrorInfo
      },
      retry: this.handleRetry,
      recoveryActions: [
        {
          label: 'Recharger la page',
          action: () => window.location.reload()
        },
        {
          label: 'Retour à l\'accueil',
          action: () => window.location.href = '/'
        }
      ]
    };

    this.setState({ errorInfo });

    // Report error if enabled
    if (this.props.enableReporting) {
      this.reportError(errorInfo);
    }

    // Call custom error handler
    this.props.onError?.(errorInfo);
  }

  private categorizeErrorSeverity = (error: Error): 'low' | 'medium' | 'high' | 'critical' => {
    const message = error.message.toLowerCase();
    
    if (message.includes('network') || message.includes('fetch')) {
      return 'medium';
    }
    
    if (message.includes('chunk') || message.includes('loading')) {
      return 'low';
    }
    
    if (message.includes('permission') || message.includes('unauthorized')) {
      return 'high';
    }
    
    return 'critical';
  };

  private categorizeErrorType = (error: Error): AppErrorInfo['category'] => {
    const message = error.message.toLowerCase();
    const stack = error.stack?.toLowerCase() || '';
    
    if (message.includes('network') || message.includes('fetch') || message.includes('xhr')) {
      return 'network';
    }
    
    if (message.includes('validation') || message.includes('invalid')) {
      return 'validation';
    }
    
    if (message.includes('permission') || message.includes('unauthorized') || message.includes('forbidden')) {
      return 'permission';
    }
    
    if (message.includes('user') || stack.includes('user')) {
      return 'user';
    }
    
    if (message.includes('system') || message.includes('internal')) {
      return 'system';
    }
    
    return 'unknown';
  };

  private handleRetry = () => {
    if (this.retryCount < this.maxRetries) {
      this.retryCount++;
      this.setState({
        hasError: false,
        error: null,
        errorInfo: null
      });
    }
  };

  private reportError = async (errorInfo: AppErrorInfo) => {
    try {
      // In a real app, you would send this to your error reporting service
      // e.g., Sentry, LogRocket, Bugsnag, etc.
      console.error('Error reported:', errorInfo);
      
      // Example API call (uncomment and modify for your needs)
      /*
      await fetch('/api/errors', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(errorInfo)
      });
      */
    } catch (reportingError) {
      console.error('Failed to report error:', reportingError);
    }
  };

  render() {
    if (this.state.hasError && this.state.errorInfo) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback(this.state.errorInfo);
      }

      // Default fallback UI
      return (
        <DefaultErrorFallback 
          errorInfo={this.state.errorInfo} 
          showDetails={this.props.showDetails}
          className={this.props.className}
        />
      );
    }

    return this.props.children;
  }
}

// Default error fallback component
interface DefaultErrorFallbackProps {
  errorInfo: AppErrorInfo;
  showDetails?: boolean;
  className?: string;
}

function DefaultErrorFallback({ errorInfo, showDetails = false, className = '' }: DefaultErrorFallbackProps) {
  const [showDetailsState, setShowDetailsState] = React.useState(showDetails);

  const getSeverityColor = () => {
    switch (errorInfo.severity) {
      case 'critical': return 'red';
      case 'high': return 'orange';
      case 'medium': return 'yellow';
      case 'low': return 'blue';
      default: return 'gray';
    }
  };

  const getSeverityIcon = () => {
    switch (errorInfo.severity) {
      case 'critical': return '🚨';
      case 'high': return '⚠️';
      case 'medium': return '⚠️';
      case 'low': return 'ℹ️';
      default: return '❓';
    }
  };

  return (
    <div className={`min-h-screen bg-gray-100 flex flex-col justify-center py-12 sm:px-6 lg:px-8 ${className}`}>
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className={`bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10 border-l-4 border-${getSeverityColor()}-500`}>
          <div className="flex items-center mb-4">
            <div className="text-2xl mr-2">{getSeverityIcon()}</div>
            <div>
              <h2 className="text-lg font-medium text-gray-900">
                Oups ! Une erreur s'est produite
              </h2>
              <p className="text-sm text-gray-600">
                Nous nous excusons pour ce désagrément. Notre équipe a été notifiée.
              </p>
            </div>
          </div>

          {errorInfo.recoveryActions && (
            <div className="mb-4">
              {errorInfo.recoveryActions.map((action, index) => (
                <button
                  key={index}
                  onClick={action.action}
                  className="mr-2 mb-2 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  {action.label}
                </button>
              ))}
            </div>
          )}

          {errorInfo.retry && (
            <button
              onClick={() => errorInfo.retry!()}
              className="mb-4 inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Réessayer ({errorInfo.context?.retryCount || 0}/{errorInfo.context?.maxRetries || 3})
            </button>
          )}

          <button
            onClick={() => setShowDetailsState(!showDetailsState)}
            className="mb-4 text-sm text-indigo-600 hover:text-indigo-500"
          >
            {showDetailsState ? 'Masquer les détails' : 'Afficher les détails'}
          </button>

          {showDetailsState && (
            <div className="mt-4 p-4 bg-gray-50 rounded-md">
              <div className="space-y-2">
                <div>
                  <strong>Message :</strong> {errorInfo.message}
                </div>
                <div>
                  <strong>Catégorie :</strong> {errorInfo.category}
                </div>
                <div>
                  <strong>Sévérité :</strong> {errorInfo.severity}
                </div>
                <div>
                  <strong>Horodatage :</strong> {errorInfo.timestamp.toLocaleString()}
                </div>
                {errorInfo.stack && (
                  <div>
                    <strong>Stack Trace :</strong>
                    <pre className="mt-1 text-xs bg-gray-100 p-2 rounded overflow-x-auto">
                      {errorInfo.stack}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Error handling utilities
export const createErrorInfo = (
  error: Error,
  overrides: Partial<AppErrorInfo> = {}
): AppErrorInfo => {
  return {
    message: error.message,
    stack: error.stack,
    timestamp: new Date(),
    userAgent: navigator.userAgent,
    url: window.location.href,
    severity: overrides.severity || 'medium',
    category: overrides.category || 'unknown',
    context: overrides.context || {},
    ...overrides
  };
};

// Network error helpers
export const handleNetworkError = (error: Error): AppErrorInfo => {
  return createErrorInfo(error, {
    category: 'network',
    severity: 'medium'
  });
};

export const handleValidationError = (error: Error): AppErrorInfo => {
  return createErrorInfo(error, {
    category: 'validation',
    severity: 'low'
  });
};

export const handlePermissionError = (error: Error): AppErrorInfo => {
  return createErrorInfo(error, {
    category: 'permission',
    severity: 'high'
  });
};

export const handleSystemError = (error: Error): AppErrorInfo => {
  return createErrorInfo(error, {
    category: 'system',
    severity: 'critical'
  });
};

// Global error handler
export const setupGlobalErrorHandling = () => {
  // Handle unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    
    // Create error info for reporting
    const errorInfo = createErrorInfo(
      event.reason instanceof Error ? event.reason : new Error(String(event.reason)),
      {
        category: 'system',
        severity: event.reason?.name === 'ChunkLoadError' ? 'low' : 'medium'
      }
    );
    
    // Report the error
    reportError(errorInfo);
  });

  // Handle general JavaScript errors
  window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
    
    const errorInfo = createErrorInfo(
      event.error || new Error(event.message),
      {
        category: 'system',
        severity: 'high'
      }
    );
    
    reportError(errorInfo);
  });
};

// Error reporting function
export const reportError = async (errorInfo: AppErrorInfo) => {
  try {
    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.group('🚨 Error Report');
      console.error('Error Info:', errorInfo);
      console.groupEnd();
    }

    // Send to error reporting service in production
    // This would be replaced with your actual error reporting service
    // e.g., Sentry, LogRocket, Bugsnag
    console.error('Error reported:', errorInfo);
  } catch (reportingError) {
    console.error('Failed to report error:', reportingError);
  }
};

// HOC for error boundary
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<ErrorBoundaryProps, 'children'>
) {
  // @ts-ignore - Complex forwardRef generic constraints - TypeScript limitation
  const WrappedComponent = React.forwardRef<any, P>((props, ref) => (
    <ErrorBoundary {...errorBoundaryProps}>
      {/* @ts-ignore - Complex generic constraint with forwardRef */}
      <Component {...props} ref={ref} />
    </ErrorBoundary>
  ));

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;
  
  return WrappedComponent;
};

// Hook for error handling
export function useErrorHandler() {
  const handleError = React.useCallback((error: Error, context?: Record<string, any>) => {
    const errorInfo = createErrorInfo(error, { context });
    reportError(errorInfo);
  }, []);

  return { handleError };
} 