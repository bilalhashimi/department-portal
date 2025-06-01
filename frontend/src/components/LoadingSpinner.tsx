import React from 'react';

const LoadingSpinner: React.FC = () => {
  return (
    <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-solid border-primary-600 border-r-transparent"></div>
  );
};

export default LoadingSpinner; 