import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'primary' | 'secondary' | 'white';
  message?: string;
  fullScreen?: boolean;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  variant = 'primary',
  message,
  fullScreen = false
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
    xl: 'w-12 h-12'
  };

  const variantClasses = {
    primary: 'border-blue-200 border-t-blue-600',
    secondary: 'border-gray-200 border-t-gray-600',
    white: 'border-white border-opacity-30 border-t-white'
  };

  const spinner = (
    <div
      className={`animate-spin rounded-full border-2 ${sizeClasses[size]} ${variantClasses[variant]}`}
      role="status"
      aria-label={message || 'Loading...'}
    >
      <span className="sr-only">{message || 'Loading...'}</span>
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 bg-white bg-opacity-75 flex items-center justify-center z-50">
        <div className="text-center">
          {spinner}
          {message && (
            <p className="mt-4 text-gray-600 font-medium">{message}</p>
          )}
        </div>
      </div>
    );
  }

  if (message) {
    return (
      <div className="flex flex-col items-center justify-center space-y-2">
        {spinner}
        <p className="text-sm text-gray-600">{message}</p>
      </div>
    );
  }

  return spinner;
};

export default LoadingSpinner; 