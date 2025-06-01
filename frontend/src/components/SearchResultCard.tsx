import React from 'react';
import type { SearchResult } from '../services/api';
import { apiService } from '../services/api';

interface SearchResultCardProps {
  result: SearchResult;
  onSelect?: (documentId: string) => void;
  searchQuery: string;
}

const SearchResultCard: React.FC<SearchResultCardProps> = ({ result, onSelect, searchQuery }) => {
  const { document, score, snippet } = result;

  const handleDownload = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      console.log('📥 Downloading document:', document.title);
      const blob = await apiService.downloadDocument(document.id);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = window.document.createElement('a');
      a.href = url;
      a.download = `${document.title}.${document.file_type.toLowerCase()}`;
      window.document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      window.document.body.removeChild(a);
      
      // Record view
      await apiService.viewDocument(document.id);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const handleView = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      console.log('👁️ Viewing document:', document.title);
      
      // For PDFs and text files, fetch and open in new tab
      if (document.file_type.toLowerCase() === 'pdf' || document.file_type.toLowerCase() === 'txt') {
        // Fetch the file with authentication
        const response = await fetch(`http://localhost:8000/api/v1/documents/${document.id}/preview/`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json',
          },
          credentials: 'include'
        });
        
        if (!response.ok) {
          throw new Error('Failed to fetch document');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        
        // Open in new tab
        const newWindow = window.open(url, '_blank');
        
        if (!newWindow) {
          // Fallback: download if popup blocked
          await handleDownload(e);
          return;
        }
        
        // Clean up the URL after a delay
        setTimeout(() => {
          window.URL.revokeObjectURL(url);
        }, 10000);
        
      } else {
        // For other file types, just download them
        await handleDownload(e);
        return;
      }
      
      // Record the view
      await apiService.viewDocument(document.id);
      
    } catch (error) {
      console.error('View failed:', error);
      // Fallback to download
      await handleDownload(e);
    }
  };

  const handleClick = () => {
    if (onSelect) {
      onSelect(document.id);
    }
  };

  const highlightText = (text: string, query: string) => {
    if (!query) return text;
    
    const regex = new RegExp(`(${query})`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, index) => 
      regex.test(part) ? (
        <mark key={index} className="bg-yellow-200 px-1 rounded">
          {part}
        </mark>
      ) : part
    );
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'published':
        return 'bg-green-100 text-green-800';
      case 'draft':
        return 'bg-gray-100 text-gray-800';
      case 'review':
        return 'bg-yellow-100 text-yellow-800';
      case 'approved':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div 
      className="search-result-card group bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow duration-200 cursor-pointer"
      onClick={handleClick}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 group-hover:text-primary-600 transition-colors duration-200">
            {highlightText(document.title, searchQuery)}
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            by {document.created_by_name} • {document.category_name}
          </p>
        </div>
        <div className="flex items-center space-x-2 ml-4">
          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(document.status)}`}>
            {document.status}
          </span>
          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getPriorityColor(document.priority)}`}>
            {document.priority}
          </span>
        </div>
      </div>

      {snippet && (
        <p className="text-gray-700 mb-3 line-clamp-2">
          {highlightText(snippet, searchQuery)}
        </p>
      )}

      <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
        <div className="flex items-center space-x-4">
          <span className="flex items-center">
            📄 {document.file_type.toUpperCase()}
          </span>
          <span>
            {document.file_size_mb} MB
          </span>
          <span>
            v{document.version}
          </span>
        </div>
        <div className="flex items-center space-x-4">
          <span>
            {formatDate(document.updated_at)}
          </span>
          <span className="text-primary-600 font-medium">
            {Math.round(score * 100)}% match
          </span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center space-x-3 pt-3 border-t border-gray-100">
        <button
          onClick={handleView}
          className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors duration-200 text-sm font-medium"
        >
          <span>👁️</span>
          <span>View</span>
        </button>
        <button
          onClick={handleDownload}
          className="flex items-center space-x-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors duration-200 text-sm font-medium"
        >
          <span>⬇️</span>
          <span>Download</span>
        </button>
        <div className="flex-1 text-right">
          <span className="text-xs text-gray-400">Click to select</span>
        </div>
      </div>
    </div>
  );
};

export default SearchResultCard; 