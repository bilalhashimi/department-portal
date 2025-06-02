import React, { useState } from 'react';
import type { SearchResult } from '../services/api';

interface DocumentListProps {
  documents: SearchResult[];
  onDocumentSelect?: (documentId: string) => void;
  onDocumentView?: (documentId: string) => void;
  onDocumentDownload?: (documentId: string) => void;
  onDocumentDelete?: (documentId: string) => void;
  onDocumentsBulkDelete?: (documentIds: string[]) => void;
  onDocumentToggleImportant?: (documentId: string, isImportant: boolean) => void;
  isLoading?: boolean;
  selectedView: string;
  isMobile?: boolean;
}

const DocumentList: React.FC<DocumentListProps> = ({
  documents,
  onDocumentView,
  onDocumentDownload,
  onDocumentsBulkDelete,
  onDocumentToggleImportant,
  isLoading = false,
  selectedView,
  isMobile = false
}) => {
  const [selectedDocuments, setSelectedDocuments] = useState<Set<string>>(new Set());
  const [hoveredDocument, setHoveredDocument] = useState<string | null>(null);

  const handleSelectDocument = (documentId: string) => {
    const newSelected = new Set(selectedDocuments);
    if (newSelected.has(documentId)) {
      newSelected.delete(documentId);
    } else {
      newSelected.add(documentId);
    }
    setSelectedDocuments(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedDocuments.size === documents.length) {
      setSelectedDocuments(new Set());
    } else {
      setSelectedDocuments(new Set(documents.map(doc => doc.document.id)));
    }
  };

  const handleDocumentClick = (documentId: string) => {
    // Open the document for viewing when clicked
    onDocumentView?.(documentId);
  };

  const handleStarClick = (e: React.MouseEvent, documentId: string) => {
    e.stopPropagation();
    const document = documents.find(doc => doc.document.id === documentId);
    const isCurrentlyImportant = document?.document.priority === 'high';
    onDocumentToggleImportant?.(documentId, !isCurrentlyImportant);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (filename: string): string => {
    const extension = filename.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'pdf': return '📄';
      case 'doc':
      case 'docx': return '📝';
      case 'xls':
      case 'xlsx': return '📊';
      case 'ppt':
      case 'pptx': return '📈';
      case 'txt': return '📋';
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif': return '🖼️';
      default: return '📎';
    }
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
    
    if (diffInHours < 24) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (diffInHours < 24 * 7) {
      return date.toLocaleDateString([], { weekday: 'short' });
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
  };

  const getViewTitle = (view: string): string => {
    switch (view) {
      case 'all': return 'All Documents';
      case 'important': return 'Important Documents';
      case 'recent': return 'Recent Documents';
      case 'shared': return 'Shared with me';
      case 'starred': return 'Starred Documents';
      case 'drafts': return 'Draft Documents';
      default: 
        if (view.startsWith('category:')) {
          const category = view.replace('category:', '');
          return category.charAt(0).toUpperCase() + category.slice(1);
        }
        return 'Documents';
    }
  };

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading documents...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 bg-white overflow-hidden">
      {/* Toolbar */}
      <div className="border-b border-gray-200 px-3 lg:px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3 lg:space-x-4">
            {!isMobile && (
              <input
                type="checkbox"
                checked={documents.length > 0 && selectedDocuments.size === documents.length}
                onChange={handleSelectAll}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
            )}
            
            {selectedDocuments.size > 0 && (
              <div className="flex items-center space-x-2">
                <button 
                  className="text-gray-500 hover:text-red-600 p-1 touch-manipulation"
                  onClick={() => {
                    if (confirm(`Delete ${selectedDocuments.size} selected document(s)?`)) {
                      onDocumentsBulkDelete?.(Array.from(selectedDocuments));
                      setSelectedDocuments(new Set());
                    }
                  }}
                  title="Delete selected documents"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
                <button 
                  className="text-gray-500 hover:text-blue-600 p-1 touch-manipulation"
                  onClick={() => {
                    Array.from(selectedDocuments).forEach(id => onDocumentDownload?.(id));
                    setSelectedDocuments(new Set());
                  }}
                  title="Download selected documents"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                </button>
                <span className="text-sm text-gray-600">
                  {selectedDocuments.size} selected
                </span>
              </div>
            )}
          </div>
          
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <span className="hidden sm:inline">{documents.length} documents</span>
            <span className="sm:hidden">{documents.length}</span>
          </div>
        </div>
      </div>

      {/* Header */}
      <div className="px-3 lg:px-4 py-4 lg:py-6 border-b border-gray-200">
        <h1 className={`${isMobile ? 'text-xl' : 'text-2xl'} font-medium text-gray-900`}>
          {getViewTitle(selectedView)}
        </h1>
        {documents.length > 0 && (
          <p className="text-sm text-gray-600 mt-1">
            {documents.length} document{documents.length !== 1 ? 's' : ''} available
          </p>
        )}
      </div>

      {/* Document List */}
      <div className="divide-y divide-gray-100 overflow-y-auto" style={{ height: 'calc(100vh - 200px)' }}>
        {documents.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 px-4">
            <div className="text-gray-400 text-6xl mb-4">📄</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No documents found</h3>
            <p className="text-gray-600 text-center max-w-md text-sm lg:text-base">
              {selectedView === 'all' 
                ? "It looks like there are no documents available. Try uploading some documents or check your permissions."
                : `No documents found in ${getViewTitle(selectedView).toLowerCase()}. Try searching or check other categories.`
              }
            </p>
          </div>
        ) : (
          documents.map((result) => (
            <div
              key={result.document.id}
              className={`px-3 lg:px-4 py-3 lg:py-4 hover:bg-gray-50 active:bg-gray-100 cursor-pointer transition-colors touch-manipulation ${
                selectedDocuments.has(result.document.id) ? 'bg-blue-50' : ''
              }`}
              onMouseEnter={() => !isMobile && setHoveredDocument(result.document.id)}
              onMouseLeave={() => !isMobile && setHoveredDocument(null)}
              onClick={() => handleDocumentClick(result.document.id)}
            >
              <div className={`flex items-start ${isMobile ? 'space-x-3' : 'space-x-4'}`}>
                {/* Mobile layout: Checkbox only for selection mode */}
                {!isMobile && (
                  <input
                    type="checkbox"
                    checked={selectedDocuments.has(result.document.id)}
                    onChange={(e) => {
                      e.stopPropagation();
                      handleSelectDocument(result.document.id);
                    }}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mt-1"
                  />
                )}

                {/* File Icon */}
                <div className={`${isMobile ? 'text-xl' : 'text-2xl'} mt-1`}>
                  {getFileIcon(result.document.title)}
                </div>

                {/* Document Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0 pr-2">
                      <h3 className={`${isMobile ? 'text-base' : 'text-sm'} font-medium text-gray-900 truncate`}>
                        {result.document.title}
                      </h3>
                      <p className={`${isMobile ? 'text-sm' : 'text-sm'} text-gray-600 truncate mt-1`}>
                        {result.document.description || 'No description available'}
                      </p>
                      {result.snippet && !isMobile && (
                        <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                          ...{result.snippet}...
                        </p>
                      )}
                    </div>

                    <div className="flex items-center space-x-2 lg:space-x-4">
                      {/* Star Button */}
                      <button 
                        className={`transition-colors p-1 touch-manipulation ${
                          result.document.priority === 'high' 
                            ? 'text-yellow-400 hover:text-yellow-500' 
                            : 'text-gray-300 hover:text-yellow-400'
                        }`}
                        onClick={(e) => handleStarClick(e, result.document.id)}
                        title={result.document.priority === 'high' ? 'Remove from important' : 'Mark as important'}
                      >
                        <svg className={`${isMobile ? 'w-5 h-5' : 'w-4 h-4'}`} fill={result.document.priority === 'high' ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                        </svg>
                      </button>

                      {/* Download button - always visible on mobile, hover on desktop */}
                      {(isMobile || hoveredDocument === result.document.id) && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onDocumentDownload?.(result.document.id);
                          }}
                          className="p-1 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100 touch-manipulation"
                          title="Download document"
                        >
                          <svg className={`${isMobile ? 'w-5 h-5' : 'w-4 h-4'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                          </svg>
                        </button>
                      )}

                      {/* Metadata */}
                      <div className="text-right text-xs text-gray-500">
                        <div>{formatDate(result.document.created_at)}</div>
                        {result.document.file_size_mb && !isMobile && (
                          <div className="mt-1">{formatFileSize(result.document.file_size_mb * 1024 * 1024)}</div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Category and Status as tags */}
                  <div className={`flex flex-wrap gap-1 ${isMobile ? 'mt-2' : 'mt-2'}`}>
                    <span className={`inline-flex items-center px-2 py-1 rounded-full ${isMobile ? 'text-xs' : 'text-xs'} bg-blue-100 text-blue-700`}>
                      {result.document.category_name}
                    </span>
                    <span className={`inline-flex items-center px-2 py-1 rounded-full ${isMobile ? 'text-xs' : 'text-xs'} bg-green-100 text-green-700`}>
                      {result.document.status}
                    </span>
                    {result.document.priority && result.document.priority !== 'medium' && (
                      <span className={`inline-flex items-center px-2 py-1 rounded-full ${isMobile ? 'text-xs' : 'text-xs'} ${
                        result.document.priority === 'high' ? 'bg-orange-100 text-orange-700' :
                        result.document.priority === 'critical' ? 'bg-red-100 text-red-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {result.document.priority}
                      </span>
                    )}
                    {/* Show file size on mobile as a tag */}
                    {isMobile && result.document.file_size_mb && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-700">
                        {formatFileSize(result.document.file_size_mb * 1024 * 1024)}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default DocumentList; 