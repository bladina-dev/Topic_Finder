import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary card">
          <div className="error-icon">💥</div>
          <h2 className="error-title">Something went wrong</h2>
          <p className="error-msg">{this.state.error?.message || 'A catastrophic UI error occurred.'}</p>
          <button 
            className="btn btn-primary" 
            onClick={() => window.location.reload()}
          >
            🔄 Reload Dashboard
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
