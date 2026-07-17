import * as React from 'react'
import { ErrorState } from '@/components/common/ErrorState'

interface Props {
  children: React.ReactNode
}

interface State {
  hasError: boolean
}

export class ErrorBoundary extends React.Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error: unknown) {
    console.error('Unhandled UI error:', error)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-[60vh] items-center justify-center">
          <ErrorState
            title="This page hit a snag"
            description="An unexpected error occurred while rendering this view. Reloading usually fixes it."
            onRetry={() => window.location.reload()}
          />
        </div>
      )
    }
    return this.props.children
  }
}
