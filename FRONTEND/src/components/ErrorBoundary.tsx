import { Component, ErrorInfo, ReactNode } from "react"
import { AlertTriangle, RefreshCw } from "lucide-react"

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Unhandled Error Caught by ErrorBoundary:", error, errorInfo)
  }

  public handleReset = () => {
    this.setState({ hasError: false, error: null })
    window.location.reload()
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-background text-foreground flex items-center justify-center p-6">
          <div className="w-full max-w-md bg-card border border-border rounded-2xl p-8 shadow-2xl space-y-6 text-center">
            <div className="w-16 h-16 rounded-full bg-danger/10 text-danger flex items-center justify-center mx-auto">
              <AlertTriangle size={32} />
            </div>
            <div className="space-y-2">
              <h2 className="text-xl font-bold">Something Went Wrong</h2>
              {/* NOTE: Class components cannot use hooks; these strings remain in English */}
              <p className="text-xs text-muted-foreground">
                An unexpected application rendering error occurred.
              </p>
              {this.state.error && (
                <div className="p-3 bg-muted/40 border border-border rounded-xl text-left text-xs text-danger font-mono overflow-auto max-h-32">
                  {this.state.error.message}
                </div>
              )}
            </div>
            <button
              onClick={this.handleReset}
              className="btn-primary w-full py-3 justify-center text-xs font-bold shadow-lg"
            >
              <RefreshCw size={14} />
              <span>Reload Application</span>
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
