import React, { useState, useEffect } from 'react';
import './App.css';
import LoadingSpinner from './components/LoadingSpinner';
import AIChatBot from './components/AIChatBot';
import Sidebar from './components/Sidebar';
import TopSearchBar from './components/TopSearchBar';
import DocumentList from './components/DocumentList';
import DocumentUpload from './components/DocumentUpload';
import AdminSettings from './components/AdminSettings';
import AdminSettingsTest from './tests/AdminSettingsTest';
import { apiService } from './services/api';
import type { SearchResult } from './services/api';
import { Toaster } from 'react-hot-toast';

function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [healthStatus, setHealthStatus] = useState<string>('checking');
  const [error, setError] = useState<string | null>(null);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [showAIChat, setShowAIChat] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showAdminSettings, setShowAdminSettings] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [showTestSuite, setShowTestSuite] = useState(false);
  const [aiChatEnabled, setAiChatEnabled] = useState(true);
  
  // Mobile responsiveness states
  const [isMobile, setIsMobile] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  
  // New states for Gmail-like interface
  const [selectedView, setSelectedView] = useState('all');
  const [documents, setDocuments] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [currentQuery, setCurrentQuery] = useState('');

  useEffect(() => {
    console.log('🚀 App starting up...');
    
    const checkAppStatus = async () => {
      try {
        console.log('📱 Checking authentication status...');
        // Check if user is authenticated
        const authStatus = apiService.isAuthenticated();
        setIsAuthenticated(authStatus);
        console.log('🔐 Authentication status:', authStatus);

        // Check if user is admin
        if (authStatus) {
          try {
            const adminStatus = await apiService.isAdmin();
            setIsAdmin(adminStatus);
            console.log('👑 Admin status:', adminStatus);
          } catch (error) {
            console.log('Failed to check admin status:', error);
            setIsAdmin(false);
          }
        }

        // Check backend health
        console.log('🏥 Checking backend health...');
        try {
          const healthResponse = await apiService.healthCheck();
          console.log('✅ Health check response:', healthResponse);
          setHealthStatus('healthy');
          
          // Load initial documents if authenticated
          if (authStatus) {
            await loadDocuments('all');
          }
        } catch (error) {
          console.error('❌ Health check failed:', error);
          setHealthStatus('unavailable');
          setError(`Backend connection failed: ${error}`);
        }
      } catch (error) {
        console.error('💥 Error checking app status:', error);
        setError(`App initialization error: ${error}`);
      } finally {
        console.log('✅ App initialization complete');
        setIsLoading(false);
      }
    };

    checkAppStatus();
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      checkAIChatStatus();
    }
  }, [isAuthenticated]);

  const checkAIChatStatus = async () => {
    try {
      const enabled = await apiService.isAIChatEnabled();
      setAiChatEnabled(enabled);
    } catch (error) {
      // Default to enabled if we can't check
      setAiChatEnabled(true);
    }
  };

  // Load documents based on view
  const loadDocuments = async (view: string, query?: string) => {
    setIsSearching(true);
    try {
      if (query && query.trim()) {
        // Search documents
        const response = await apiService.searchDocuments(query, 50);
        setDocuments(filterDocumentsByView(response.results, view));
        setCurrentQuery(query);
      } else {
        // Load documents using the view-specific API
        try {
          const documentsData = await apiService.getDocumentsByView(view);
          console.log(`📄 Documents for view "${view}":`, documentsData);
          // Transform to SearchResult format for consistency
          const transformedResults = documentsData.map(doc => ({
            document: doc,
            score: 1.0,
            snippet: doc.description || '',
            metadata: {}
          }));
          // For view-specific queries, we rely more on backend filtering
          // but still apply frontend filtering for additional refinement
          setDocuments(filterDocumentsByView(transformedResults, view));
          setCurrentQuery('');
        } catch (error) {
          // Fallback to search with empty query if documents API fails
          console.log('Fallback to search API');
          const response = await apiService.searchDocuments('', 50);
          setDocuments(filterDocumentsByView(response.results, view));
          setCurrentQuery('');
        }
      }
    } catch (error) {
      console.error('Error loading documents:', error);
      setDocuments([]);
    } finally {
      setIsSearching(false);
    }
  };

  // Filter documents based on the selected view
  const filterDocumentsByView = (allDocuments: SearchResult[], view: string): SearchResult[] => {
    console.log(`🎯 Frontend filtering ${allDocuments.length} documents for view: "${view}"`);
    
    switch (view) {
      case 'all':
        return allDocuments;
      case 'important':
        return allDocuments.filter(doc => doc.document.priority === 'high' || doc.document.priority === 'critical');
      case 'recent':
        return allDocuments.filter(doc => {
          const date = new Date(doc.document.created_at);
          const now = new Date();
          const diffInDays = (now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24);
          return diffInDays <= 7;
        });
      case 'shared':
        // Backend already handles shared filtering with ?shared=true
        // Don't apply additional frontend filtering for shared documents
        console.log(`📤 Shared view: Backend returned ${allDocuments.length} shared documents`);
        return allDocuments;
      case 'starred':
        return allDocuments.filter(doc => doc.document.priority === 'high'); // For now, use high priority as starred
      case 'drafts':
        const draftDocs = allDocuments.filter(doc => {
          console.log(`📝 Document "${doc.document.title}" status: "${doc.document.status}"`);
          return doc.document.status === 'draft';
        });
        console.log(`✅ Found ${draftDocs.length} draft documents out of ${allDocuments.length} total`);
        return draftDocs;
      default:
        if (view.startsWith('category:')) {
          const category = view.replace('category:', '');
          return allDocuments.filter(doc => 
            doc.document.category_name.toLowerCase().includes(category.toLowerCase())
          );
        }
        return allDocuments;
    }
  };

  // Handle view change from sidebar
  const handleViewChange = (view: string) => {
    setSelectedView(view);
    loadDocuments(view, currentQuery);
  };

  // Handle search from top search bar
  const handleSearch = (query: string) => {
    loadDocuments(selectedView, query);
  };

  const handleDocumentSelect = (documentId: string) => {
    console.log('Selected document:', documentId);
    // Here you could navigate to document details, open a modal, etc.
  };

  const handleDocumentView = async (documentId: string) => {
    try {
      await apiService.previewDocument(documentId);
      console.log('Document viewed:', documentId);
    } catch (error) {
      console.error('Error viewing document:', error);
    }
  };

  const handleDocumentDownload = async (documentId: string) => {
    try {
      const blob = await apiService.downloadDocument(documentId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      
      // Find the document to get its title
      const foundDocument = documents.find(doc => doc.document.id === documentId);
      a.download = foundDocument?.document.title || `document-${documentId}`;
      
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      console.log('Document downloaded:', documentId);
    } catch (error) {
      console.error('Error downloading document:', error);
    }
  };

  const handleDocumentToggleImportant = async (documentId: string, isImportant: boolean) => {
    try {
      const priority = isImportant ? 'high' : 'medium';
      await apiService.updateDocumentPriority(documentId, priority);
      
      // Update the local state
      setDocuments(prevDocs => 
        prevDocs.map(doc => 
          doc.document.id === documentId 
            ? { ...doc, document: { ...doc.document, priority } }
            : doc
        )
      );
      
      console.log(`Document ${documentId} priority updated to ${priority}`);
    } catch (error) {
      console.error('Error updating document priority:', error);
    }
  };

  const handleDocumentDelete = async (documentId: string) => {
    try {
      if (confirm('Are you sure you want to delete this document?')) {
        await apiService.deleteDocument(documentId);
        
        // Remove the document from local state
        setDocuments(prevDocs => 
          prevDocs.filter(doc => doc.document.id !== documentId)
        );
        
        console.log('Document deleted:', documentId);
      }
    } catch (error) {
      console.error('Error deleting document:', error);
    }
  };

  const handleDocumentsBulkDelete = async (documentIds: string[]) => {
    try {
      await apiService.deleteDocuments(documentIds);
      
      // Remove the documents from local state
      setDocuments(prevDocs => 
        prevDocs.filter(doc => !documentIds.includes(doc.document.id))
      );
      
      console.log('Documents deleted:', documentIds);
    } catch (error) {
      console.error('Error deleting documents:', error);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoggingIn(true);
    
    try {
      await apiService.login(loginForm);
      setIsAuthenticated(true);
      setShowLoginModal(false);
      setLoginForm({ email: '', password: '' });
      
      // Check admin status after login
      try {
        const adminStatus = await apiService.isAdmin();
        setIsAdmin(adminStatus);
      } catch (error) {
        setIsAdmin(false);
      }
      
      // Load documents after login
      await loadDocuments('all');
    } catch (error) {
      console.error('Login failed:', error);
    } finally {
      setIsLoggingIn(false);
    }
  };

  const handleLogout = async () => {
    try {
      await apiService.logout();
      setIsAuthenticated(false);
      setIsAdmin(false);
      setDocuments([]);
      setShowAdminSettings(false);
      setShowTestSuite(false);
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const handleRefresh = () => {
    console.log(`🔄 Refreshing ${selectedView} view`);
    loadDocuments(selectedView, currentQuery);
  };

  // Calculate document counts for sidebar
  const documentCounts = {
    all: documents.length,
    important: documents.filter(doc => doc.document.priority === 'high').length,
    recent: documents.filter(doc => {
      const date = new Date(doc.document.created_at);
      const now = new Date();
      const diffInDays = (now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24);
      return diffInDays <= 7;
    }).length,
    // For shared count, use the current documents count when in shared view
    // Otherwise, it's not accurate since we don't have all shared docs loaded
    shared: selectedView === 'shared' ? documents.length : 0,
    starred: 0, // TODO: Implement starred functionality
    drafts: documents.filter(doc => doc.document.status === 'draft').length
  };

  console.log('🎨 Rendering App:', { isLoading, healthStatus, isAuthenticated, error });

  // Check screen size and set mobile state
  useEffect(() => {
    const checkScreenSize = () => {
      setIsMobile(window.innerWidth < 768);
      if (window.innerWidth >= 768) {
        setSidebarOpen(false); // Close sidebar on desktop
      }
    };

    checkScreenSize();
    window.addEventListener('resize', checkScreenSize);
    return () => window.removeEventListener('resize', checkScreenSize);
  }, []);

  // Close sidebar when clicking outside on mobile
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (isMobile && sidebarOpen) {
        const sidebar = document.getElementById('mobile-sidebar');
        const hamburger = document.getElementById('hamburger-button');
        const target = event.target as Node;
        
        if (sidebar && !sidebar.contains(target) && hamburger && !hamburger.contains(target)) {
          setSidebarOpen(false);
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isMobile, sidebarOpen]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner />
          <p className="mt-4 text-gray-600">Loading Department Portal...</p>
          {error && (
            <p className="mt-2 text-red-600 text-sm">{error}</p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-30">
        <div className="px-4 lg:px-6">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              {/* Mobile Hamburger Menu */}
              {isMobile && isAuthenticated && healthStatus === 'healthy' && !showAdminSettings && (
                <button
                  id="hamburger-button"
                  onClick={() => setSidebarOpen(!sidebarOpen)}
                  className="p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
                  aria-label="Toggle sidebar"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    {sidebarOpen ? (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    ) : (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                    )}
                  </svg>
                </button>
              )}
              
              {/* Logo/Title */}
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => {
                    setShowAdminSettings(false);
                    setShowTestSuite(false);
                    // Refresh documents when returning to main view
                    setTimeout(() => loadDocuments(selectedView, currentQuery), 100);
                  }}
                  className="text-xl lg:text-2xl font-bold text-gray-900 hover:text-blue-600 transition-colors"
                >
                  Department Portal
                </button>
                <span className="hidden sm:inline-flex px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                  AI-Powered
                </span>
                {showTestSuite && (
                  <span className="inline-flex px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                    Test Mode
                  </span>
                )}
                {showAdminSettings && (
                  <span className="inline-flex px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded-full">
                    Admin Mode
                  </span>
                )}
              </div>
            </div>

            {/* Desktop/Tablet Search Bar */}
            {isAuthenticated && healthStatus === 'healthy' && !isMobile && !showAdminSettings && (
              <div className="flex-1 max-w-lg mx-8">
                <TopSearchBar 
                  onSearch={handleSearch}
                  isLoading={isSearching}
                />
              </div>
            )}
            
            <div className="flex items-center space-x-2 lg:space-x-4">
              {/* System Status */}
              <div className="hidden sm:flex items-center">
                <div className={`w-2 h-2 rounded-full mr-2 ${
                  healthStatus === 'healthy' ? 'bg-green-500' : 
                  healthStatus === 'unavailable' ? 'bg-red-500' : 'bg-yellow-500'
                }`}></div>
                <span className="text-xs lg:text-sm text-gray-600">
                  {healthStatus === 'healthy' ? 'Online' : 
                   healthStatus === 'unavailable' ? 'Offline' : 'Checking...'}
                </span>
              </div>
              
              {/* Admin Settings Button */}
              {isAuthenticated && isAdmin && (
                <button
                  onClick={() => {
                    if (showAdminSettings) {
                      // Refresh documents when leaving admin settings
                      setShowAdminSettings(false);
                      setShowTestSuite(false);
                      // Refresh the current view
                      setTimeout(() => loadDocuments(selectedView, currentQuery), 100);
                    } else {
                      setShowAdminSettings(true);
                      setShowTestSuite(false);
                    }
                  }}
                  className={`flex items-center space-x-1 lg:space-x-2 px-2 lg:px-3 py-2 rounded-lg border transition-colors ${
                    showAdminSettings
                      ? 'bg-purple-600 text-white border-purple-600' 
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  }`}
                  title="Admin Settings"
                >
                  <span className="text-sm">⚙️</span>
                  <span className="hidden sm:inline text-sm font-medium">Settings</span>
                </button>
              )}
              
              {/* Test Suite Button */}
              {isAuthenticated && isAdmin && (
                <button
                  onClick={() => {
                    if (showTestSuite) {
                      // Refresh documents when leaving test suite
                      setShowTestSuite(false);
                      setShowAdminSettings(false);
                      // Refresh the current view
                      setTimeout(() => loadDocuments(selectedView, currentQuery), 100);
                    } else {
                      setShowTestSuite(true);
                      setShowAdminSettings(false);
                    }
                  }}
                  className={`flex items-center space-x-1 lg:space-x-2 px-2 lg:px-3 py-2 rounded-lg border transition-colors ${
                    showTestSuite
                      ? 'bg-green-600 text-white border-green-600' 
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  }`}
                  title="Test Suite"
                >
                  <span className="text-sm">🧪</span>
                  <span className="hidden sm:inline text-sm font-medium">Tests</span>
                </button>
              )}
              
              {/* AI Chat Button */}
              {isAuthenticated && !showAdminSettings && !showTestSuite && aiChatEnabled && (
                <button
                  onClick={() => setShowAIChat(!showAIChat)}
                  className={`flex items-center space-x-1 lg:space-x-2 px-2 lg:px-3 py-2 rounded-lg border transition-colors ${
                    showAIChat 
                      ? 'bg-blue-600 text-white border-blue-600' 
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  }`}
                  title="AI Document Assistant"
                >
                  <span className="text-sm">🤖</span>
                  <span className="hidden sm:inline text-sm font-medium">AI Chat</span>
                </button>
              )}
              
              {/* Auth Buttons */}
              {!isAuthenticated ? (
                <button 
                  onClick={() => setShowLoginModal(true)}
                  className="btn-primary text-sm lg:text-base px-3 lg:px-4 py-2"
                >
                  Sign In
                </button>
              ) : (
                <button 
                  onClick={handleLogout}
                  className="btn-secondary text-sm lg:text-base px-3 lg:px-4 py-2"
                >
                  <span className="hidden sm:inline">Sign Out</span>
                  <span className="sm:hidden">Out</span>
                </button>
              )}
            </div>
          </div>

          {/* Mobile Search Bar */}
          {isAuthenticated && healthStatus === 'healthy' && isMobile && !showAdminSettings && (
            <div className="pb-4">
              <TopSearchBar 
                onSearch={handleSearch}
                isLoading={isSearching}
              />
            </div>
          )}
        </div>
      </header>

      {/* Login Modal */}
      {showLoginModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 lg:p-8 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl lg:text-2xl font-bold text-gray-900">Sign In</h2>
              <button 
                onClick={() => setShowLoginModal(false)}
                className="text-gray-400 hover:text-gray-600 p-2 touch-manipulation"
              >
                ✕
              </button>
            </div>
            
            <form onSubmit={handleLogin} className="space-y-4 lg:space-y-6">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  value={loginForm.email}
                  onChange={(e) => setLoginForm(prev => ({ ...prev, email: e.target.value }))}
                  className="input-field text-base"
                  placeholder="admin@portal.com"
                  required
                />
              </div>
              
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  value={loginForm.password}
                  onChange={(e) => setLoginForm(prev => ({ ...prev, password: e.target.value }))}
                  className="input-field text-base"
                  placeholder="••••••••"
                  required
                />
              </div>
              
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <p className="text-sm text-blue-800">
                  <strong>Demo Credentials:</strong><br/>
                  Email: admin@portal.com<br/>
                  Password: admin123
                </p>
              </div>
              
              <div className="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowLoginModal(false)}
                  className="btn-secondary flex-1 w-full"
                  disabled={isLoggingIn}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary flex-1 w-full"
                  disabled={isLoggingIn}
                >
                  {isLoggingIn ? <LoadingSpinner /> : 'Sign In'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="flex h-screen bg-gray-50">
        {healthStatus === 'healthy' && isAuthenticated ? (
          <>
            {showTestSuite ? (
              <AdminSettingsTest />
            ) : showAdminSettings ? (
              <AdminSettings />
            ) : (
              <>
                {/* Mobile Sidebar Overlay */}
                {isMobile && sidebarOpen && (
                  <div className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden">
                    <div 
                      id="mobile-sidebar"
                      className={`fixed left-0 top-0 h-full w-80 bg-white transform transition-transform duration-300 ease-in-out ${
                        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
                      }`}
                    >
                      <div className="pt-16"> {/* Account for header height */}
                        <Sidebar 
                          selectedView={selectedView}
                          onViewChange={(view) => {
                            handleViewChange(view);
                            setSidebarOpen(false); // Close sidebar after selection on mobile
                          }}
                          onUploadClick={() => {
                            setShowUploadModal(true);
                            setSidebarOpen(false);
                          }}
                          documentCounts={documentCounts}
                          isMobile={true}
                        />
                      </div>
                    </div>
                  </div>
                )}
                
                {/* Desktop Sidebar */}
                {!isMobile && (
                  <Sidebar 
                    selectedView={selectedView}
                    onViewChange={handleViewChange}
                    onUploadClick={() => setShowUploadModal(true)}
                    documentCounts={documentCounts}
                    isMobile={false}
                  />
                )}
                
                {/* Document List */}
                <div className="flex-1 flex flex-col min-w-0">
                  <DocumentList 
                    documents={documents}
                    onDocumentSelect={handleDocumentSelect}
                    onDocumentView={handleDocumentView}
                    onDocumentDownload={handleDocumentDownload}
                    onDocumentToggleImportant={handleDocumentToggleImportant}
                    onDocumentDelete={handleDocumentDelete}
                    onDocumentsBulkDelete={handleDocumentsBulkDelete}
                    isLoading={isSearching}
                    selectedView={selectedView}
                    isMobile={isMobile}
                    onRefresh={handleRefresh}
                  />
                </div>
              </>
            )}
          </>
        ) : !isAuthenticated ? (
          <div className="flex-1 flex items-center justify-center p-4">
            <div className="max-w-md mx-auto text-center">
              <div className="bg-white rounded-lg shadow-lg p-6 lg:p-8">
                <div className="text-blue-500 text-4xl mb-4">🔐</div>
                <h2 className="text-lg lg:text-xl font-semibold text-gray-900 mb-2">
                  Welcome to Department Portal
                </h2>
                <p className="text-gray-600 mb-4 text-sm lg:text-base">
                  Please sign in to access your documents and AI-powered search.
                </p>
                <button 
                  onClick={() => setShowLoginModal(true)}
                  className="btn-primary w-full lg:w-auto"
                >
                  Sign In
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center p-4">
            <div className="max-w-md mx-auto text-center">
              <div className="bg-white rounded-lg shadow-lg p-6 lg:p-8">
                <div className="text-red-500 text-4xl mb-4">⚠️</div>
                <h2 className="text-lg lg:text-xl font-semibold text-gray-900 mb-2">
                  Service Unavailable
                </h2>
                <p className="text-gray-600 mb-4 text-sm lg:text-base">
                  The document search service is currently unavailable. Please try again later.
                </p>
                <button 
                  onClick={() => window.location.reload()} 
                  className="btn-primary w-full lg:w-auto"
                >
                  Retry
                </button>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* AI Chat Sidebar */}
      {isAuthenticated && !showAdminSettings && !showTestSuite && aiChatEnabled && (
        <div className={`fixed top-0 right-0 h-full w-96 bg-white shadow-2xl z-40 transform transition-transform duration-300 ease-in-out ${
          showAIChat ? 'translate-x-0' : 'translate-x-full'
        }`}>
          <div className="h-full flex flex-col">
            <div className="flex-1 overflow-hidden">
              <AIChatBot />
            </div>
          </div>
        </div>
      )}
      
      {/* AI Chat Overlay */}
      {isAuthenticated && showAIChat && !showAdminSettings && !showTestSuite && aiChatEnabled && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-25 z-30"
          onClick={() => setShowAIChat(false)}
        />
      )}

      {/* Document Upload Modal */}
      <DocumentUpload
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        onUploadSuccess={() => {
          // Reload documents after successful upload
          loadDocuments(selectedView, currentQuery);
        }}
      />

      {/* Toast notifications */}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
        }}
      />
    </div>
  );
}

export default App;
