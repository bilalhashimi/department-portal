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
  onRefresh?: () => void;
  isLoading?: boolean;
  selectedView: string;
  isMobile?: boolean;
}

// Confirmation Dialog Component
interface ConfirmationDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  confirmVariant?: 'danger' | 'primary';
  onConfirm: () => void;
  onCancel: () => void;
}

const ConfirmationDialog: React.FC<ConfirmationDialogProps> = ({
  isOpen,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  confirmVariant = 'primary',
  onConfirm,
  onCancel
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
        <div className="flex items-start space-x-3 mb-4">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
            confirmVariant === 'danger' ? 'bg-red-100' : 'bg-blue-100'
          }`}>
            {confirmVariant === 'danger' ? (
              <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            ) : (
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            )}
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
            <p className="text-gray-600">{message}</p>
          </div>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-3 sm:gap-2 sm:justify-end">
          <button
            onClick={onCancel}
            className="btn-secondary flex-1 sm:flex-none"
            autoFocus
          >
            {cancelText}
          </button>
          <button
            onClick={onConfirm}
            className={`flex-1 sm:flex-none ${
              confirmVariant === 'danger' ? 'btn-danger' : 'btn-primary'
            }`}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

const DocumentList: React.FC<DocumentListProps> = ({
  documents,
  onDocumentView,
  onDocumentDownload,
  onDocumentsBulkDelete,
  onDocumentToggleImportant,
  onRefresh,
  isLoading = false,
  selectedView,
  isMobile = false
}) => {
  const [selectedDocuments, setSelectedDocuments] = useState<Set<string>>(new Set());
  const [hoveredDocument, setHoveredDocument] = useState<string | null>(null);
  const [confirmDialog, setConfirmDialog] = useState<{
    isOpen: boolean;
    title: string;
    message: string;
    onConfirm: () => void;
  }>({
    isOpen: false,
    title: '',
    message: '',
    onConfirm: () => {}
  });

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

  const handleBulkDelete = () => {
    const count = selectedDocuments.size;
    setConfirmDialog({
      isOpen: true,
      title: 'Delete Documents',
      message: `Are you sure you want to delete ${count} selected document${count > 1 ? 's' : ''}? This action cannot be undone.`,
      onConfirm: () => {
        onDocumentsBulkDelete?.(Array.from(selectedDocuments));
        setSelectedDocuments(new Set());
        setConfirmDialog(prev => ({ ...prev, isOpen: false }));
      }
    });
  };

  const handleBulkDownload = () => {
    const count = selectedDocuments.size;
    if (count > 5) {
      setConfirmDialog({
        isOpen: true,
        title: 'Download Multiple Documents',
        message: `You're about to download ${count} documents. This may take some time. Do you want to continue?`,
        onConfirm: () => {
          Array.from(selectedDocuments).forEach(id => onDocumentDownload?.(id));
          setSelectedDocuments(new Set());
          setConfirmDialog(prev => ({ ...prev, isOpen: false }));
        }
      });
    } else {
      Array.from(selectedDocuments).forEach(id => onDocumentDownload?.(id));
      setSelectedDocuments(new Set());
    }
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
      case 'zip':
      case 'rar': return '📦';
      case 'mp4':
      case 'avi':
      case 'mov': return '🎥';
      case 'mp3':
      case 'wav': return '🎵';
      default: return '📎';
    }
  };

  const formatDate = (dateString: string): string => {
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
      
      if (diffInHours < 1) {
        return 'Just now';
      } else if (diffInHours < 24) {
        const hours = Math.floor(diffInHours);
        return `${hours}h ago`;
      } else if (diffInHours < 24 * 7) {
        const days = Math.floor(diffInHours / 24);
        return `${days}d ago`;
      } else {
        return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
      }
    } catch (error) {
      return 'Unknown';
    }
  };

  const getViewTitle = (view: string): string => {
    switch (view) {
      case 'all': return 'All Documents';
      case 'important': return 'High Priority Documents';
      case 'recent': return 'Recently Viewed';
      case 'shared': return 'Shared With Me';
      case 'starred': return 'Bookmarked Documents';
      case 'drafts': return 'Draft Documents';
      default: 
        if (view.startsWith('category:')) {
          const category = view.replace('category:', '');
          const formatted = category.charAt(0).toUpperCase() + category.slice(1);
          return `${formatted} Documents`;
        }
        return 'Documents';
    }
  };

  const getViewDescription = (view: string): string => {
    switch (view) {
      case 'all': return 'All documents available to you';
      case 'important': return 'Documents marked as high priority or critical';
      case 'recent': return 'Documents you\'ve viewed in the last 7 days';
      case 'shared': return 'Documents that others have shared with you';
      case 'starred': return 'Documents you\'ve bookmarked for quick access';
      case 'drafts': return 'Documents that are still in draft status';
      default: 
        if (view.startsWith('category:')) {
          const category = view.replace('category:', '');
          return `Documents in the ${category} category`;
        }
        return 'Filtered document view';
    }
  };

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <div className="loading-spinner primary h-8 w-8 mx-auto mb-4"></div>
          <p className="text-gray-600 font-medium">Loading documents...</p>
          <p className="text-gray-500 text-sm mt-1">Please wait while we fetch your documents</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 bg-white overflow-hidden">
      {/* Enhanced Toolbar */}
      <div className="border-b border-gray-200 px-3 lg:px-6 py-3 bg-gray-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3 lg:space-x-4">
            {!isMobile && documents.length > 0 && (
              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={documents.length > 0 && selectedDocuments.size === documents.length}
                  onChange={handleSelectAll}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 focus:ring-offset-2"
                  aria-label={`Select all ${documents.length} documents`}
                />
                <label className="ml-2 text-sm text-gray-600">
                  Select all
                </label>
              </div>
            )}
            
            {selectedDocuments.size > 0 && (
              <div className="flex items-center space-x-2 bg-white rounded-lg p-2 shadow-sm border">
                <button 
                  className="btn-danger btn-sm flex items-center space-x-1"
                  onClick={handleBulkDelete}
                  aria-label={`Delete ${selectedDocuments.size} selected documents`}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  <span className="hidden sm:inline">Delete</span>
                </button>
                <button 
                  className="btn-secondary btn-sm flex items-center space-x-1"
                  onClick={handleBulkDownload}
                  aria-label={`Download ${selectedDocuments.size} selected documents`}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  <span className="hidden sm:inline">Download</span>
                </button>
                <span className="text-sm text-gray-600 font-medium">
                  {selectedDocuments.size} selected
                </span>
              </div>
            )}
          </div>
          
          <div className="flex items-center space-x-3 text-sm text-gray-600">
            <div className="flex items-center space-x-1">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span className="font-medium">{documents.length}</span>
              <span className="hidden sm:inline">documents</span>
            </div>
          </div>
        </div>
      </div>

      {/* Enhanced Header */}
      <div className="px-3 lg:px-6 py-4 lg:py-6 border-b border-gray-100 bg-white">
        <div className="flex items-start justify-between">
          <div>
            <h1 className={`${isMobile ? 'text-xl' : 'text-2xl'} font-semibold text-gray-900 mb-1`}>
              {getViewTitle(selectedView)}
            </h1>
            <p className="text-sm text-gray-600">
              {getViewDescription(selectedView)}
            </p>
            {documents.length > 0 && (
              <p className="text-xs text-gray-500 mt-1">
                Showing {documents.length} document{documents.length !== 1 ? 's' : ''}
              </p>
            )}
          </div>
          
          {/* Quick filters or sort options could go here */}
          <div className="flex items-center space-x-2">
            <div className="text-xs text-gray-500">
              Updated just now
            </div>
          </div>
        </div>
      </div>

      {/* Enhanced Document List */}
      <div className="divide-y divide-gray-100 overflow-y-auto" style={{ height: 'calc(100vh - 240px)' }}>
        {documents.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 px-4">
            <div className="text-gray-300 text-8xl mb-6">📄</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">No documents found</h3>
            <p className="text-gray-600 text-center max-w-md text-base leading-relaxed">
              {selectedView === 'all' 
                ? "It looks like there are no documents available yet. Upload some documents to get started, or check if you have the necessary permissions."
                : selectedView === 'drafts'
                ? "No draft documents found. Documents with 'draft' status will appear here. Try uploading a new document and set its status to 'draft'."
                : selectedView === 'shared'
                ? "No shared documents found. Documents shared with you or your department will appear here."
                : `No documents found in ${getViewTitle(selectedView).toLowerCase()}. Try browsing other categories or using the search function.`
              }
            </p>
            <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200 max-w-md">
              <h4 className="font-medium text-blue-800 mb-2">💡 Quick Tips:</h4>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• Upload documents using the "Upload Document" button</li>
                <li>• Make sure documents are assigned to categories</li>
                <li>• Check document status (draft, published, etc.)</li>
                <li>• Try refreshing if you just created categories</li>
              </ul>
            </div>
            <div className="mt-6 flex flex-col sm:flex-row gap-3">
              <button className="btn-primary" onClick={onRefresh}>
                🔄 Refresh
              </button>
              <button className="btn-secondary" onClick={() => {
                // Try to trigger upload modal
                const uploadButton = document.querySelector('[data-action="upload"]') as HTMLButtonElement;
                if (uploadButton) {
                  uploadButton.click();
                } else {
                  // Fallback: scroll to sidebar
                  const sidebar = document.querySelector('[data-component="sidebar"]');
                  if (sidebar) {
                    sidebar.scrollIntoView({ behavior: 'smooth' });
                  }
                }
              }}>
                📁 Upload Document
              </button>
            </div>
          </div>
        ) : (
          documents.map((result) => (
            <div
              key={result.document.id}
              className={`px-3 lg:px-6 py-4 lg:py-5 hover:bg-gray-50 active:bg-gray-100 cursor-pointer transition-all duration-200 group ${
                selectedDocuments.has(result.document.id) ? 'bg-blue-50 border-l-4 border-blue-500' : ''
              }`}
              onMouseEnter={() => !isMobile && setHoveredDocument(result.document.id)}
              onMouseLeave={() => !isMobile && setHoveredDocument(null)}
              onClick={() => handleDocumentClick(result.document.id)}
              role="button"
              tabIndex={0}
              aria-label={`Open document: ${result.document.title}`}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  handleDocumentClick(result.document.id);
                }
              }}
            >
              <div className={`flex items-start ${isMobile ? 'space-x-3' : 'space-x-4'}`}>
                {/* Desktop Checkbox */}
                {!isMobile && (
                  <input
                    type="checkbox"
                    checked={selectedDocuments.has(result.document.id)}
                    onChange={(e) => {
                      e.stopPropagation();
                      handleSelectDocument(result.document.id);
                    }}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mt-1.5"
                    aria-label={`Select document: ${result.document.title}`}
                  />
                )}

                {/* File Icon */}
                <div className={`${isMobile ? 'text-2xl' : 'text-3xl'} mt-1 group-hover:scale-110 transition-transform duration-200`}>
                  {getFileIcon(result.document.title)}
                </div>

                {/* Document Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0 pr-3">
                      <h3 className={`${isMobile ? 'text-base' : 'text-lg'} font-semibold text-gray-900 group-hover:text-blue-600 transition-colors duration-200`}>
                        {result.document.title}
                      </h3>
                      <p className={`${isMobile ? 'text-sm' : 'text-base'} text-gray-600 mt-1 ${isMobile ? 'line-clamp-2' : 'line-clamp-1'}`}>
                        {result.document.description || 'No description available'}
                      </p>
                      {result.snippet && !isMobile && (
                        <p className="text-sm text-gray-500 mt-2 line-clamp-2 bg-gray-50 p-2 rounded-md">
                          <span className="font-medium">Search match:</span> ...{result.snippet}...
                        </p>
                      )}
                      <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                        <span>By {result.document.created_by_name}</span>
                        <span>•</span>
                        <span>{formatDate(result.document.created_at)}</span>
                        {result.document.file_size_mb && (
                          <>
                            <span>•</span>
                            <span>{formatFileSize(result.document.file_size_mb * 1024 * 1024)}</span>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex items-center space-x-2">
                      {/* Star Button */}
                      <button 
                        className={`transition-all duration-200 p-2 rounded-full hover:bg-gray-100 ${
                          result.document.priority === 'high' 
                            ? 'text-yellow-500 hover:text-yellow-600' 
                            : 'text-gray-300 hover:text-yellow-500'
                        }`}
                        onClick={(e) => handleStarClick(e, result.document.id)}
                        title={result.document.priority === 'high' ? 'Remove bookmark' : 'Add bookmark'}
                        aria-label={result.document.priority === 'high' ? 'Remove bookmark' : 'Add bookmark'}
                      >
                        <svg className={`${isMobile ? 'w-5 h-5' : 'w-5 h-5'}`} fill={result.document.priority === 'high' ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                        </svg>
                      </button>

                      {/* Download button */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDocumentDownload?.(result.document.id);
                        }}
                        className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-full transition-all duration-200"
                        title="Download document"
                        aria-label="Download document"
                      >
                        <svg className={`${isMobile ? 'w-5 h-5' : 'w-5 h-5'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                        </svg>
                      </button>
                    </div>
                  </div>

                  {/* Enhanced Status Tags */}
                  <div className={`flex flex-wrap gap-2 ${isMobile ? 'mt-3' : 'mt-3'}`}>
                    <span className="badge badge-primary">
                      {result.document.category_name}
                    </span>
                    <span className={`badge ${
                      result.document.status === 'published' ? 'badge-success' :
                      result.document.status === 'draft' ? 'badge-warning' :
                      'badge-gray'
                    }`}>
                      {result.document.status}
                    </span>
                    {result.document.priority && result.document.priority !== 'medium' && (
                      <span className={`badge ${
                        result.document.priority === 'critical' ? 'badge-danger' :
                        result.document.priority === 'high' ? 'badge-warning' :
                        'badge-gray'
                      }`}>
                        {result.document.priority === 'critical' ? '🔴 Critical' :
                         result.document.priority === 'high' ? '🟡 High' :
                         result.document.priority}
                      </span>
                    )}
                    {result.score && result.score < 1 && (
                      <span className="badge badge-gray">
                        {Math.round(result.score * 100)}% match
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Confirmation Dialog */}
      <ConfirmationDialog
        isOpen={confirmDialog.isOpen}
        title={confirmDialog.title}
        message={confirmDialog.message}
        confirmText="Yes, proceed"
        cancelText="Cancel"
        confirmVariant={confirmDialog.title.includes('Delete') ? 'danger' : 'primary'}
        onConfirm={confirmDialog.onConfirm}
        onCancel={() => setConfirmDialog(prev => ({ ...prev, isOpen: false }))}
      />
    </div>
  );
};

export default DocumentList; 