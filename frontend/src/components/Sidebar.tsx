import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';

interface SidebarProps {
  selectedView: string;
  onViewChange: (view: string) => void;
  onUploadClick: () => void;
  isMobile?: boolean;
  documentCounts?: {
    all: number;
    important: number;
    recent: number;
    shared: number;
    starred: number;
  };
}

const Sidebar: React.FC<SidebarProps> = ({ 
  selectedView, 
  onViewChange, 
  onUploadClick,
  isMobile = false,
  documentCounts = { all: 0, important: 0, recent: 0, shared: 0, starred: 0 }
}) => {
  const [isAdmin, setIsAdmin] = useState(false);

  // Check if user is admin when component mounts
  useEffect(() => {
    const checkAdminStatus = async () => {
      try {
        const adminStatus = await apiService.isAdmin();
        setIsAdmin(adminStatus);
      } catch (error) {
        console.error('Error checking admin status:', error);
        setIsAdmin(false);
      }
    };

    checkAdminStatus();
  }, []);

  const menuItems = [
    {
      id: 'all',
      label: 'All Documents',
      icon: '📄',
      count: documentCounts.all,
      description: 'All available documents'
    },
    {
      id: 'important',
      label: 'Important',
      icon: '⭐',
      count: documentCounts.important,
      description: 'High priority documents'
    },
    {
      id: 'recent',
      label: 'Recent',
      icon: '🕒',
      count: documentCounts.recent,
      description: 'Recently viewed documents'
    },
    {
      id: 'shared',
      label: 'Shared with me',
      icon: '👥',
      count: documentCounts.shared,
      description: 'Documents shared by others'
    },
    {
      id: 'starred',
      label: 'Starred',
      icon: '⭐',
      count: documentCounts.starred,
      description: 'Your starred documents'
    },
    {
      id: 'drafts',
      label: 'Drafts',
      icon: '📝',
      count: 0,
      description: 'Draft documents'
    }
  ];

  const categories = [
    {
      id: 'policies',
      label: 'Policies',
      icon: '📋',
      color: 'text-blue-600'
    },
    {
      id: 'reports',
      label: 'Reports',
      icon: '📊',
      color: 'text-green-600'
    },
    {
      id: 'forms',
      label: 'Forms',
      icon: '📝',
      color: 'text-purple-600'
    },
    {
      id: 'manuals',
      label: 'Manuals',
      icon: '📚',
      color: 'text-orange-600'
    }
  ];

  if (isMobile) {
    return (
      <div className="w-full h-full bg-white flex flex-col">
        {/* Mobile Header */}
        <div className="flex-shrink-0 bg-gradient-to-r from-blue-600 to-blue-700 text-white p-4 shadow-lg">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-white bg-opacity-20 rounded-lg flex items-center justify-center">
              <span className="text-lg">📂</span>
            </div>
            <div>
              <h2 className="font-semibold text-lg">Department Portal</h2>
              <p className="text-blue-100 text-sm">Document Management</p>
            </div>
          </div>
        </div>

        {/* Upload Button */}
        <div className="flex-shrink-0 p-4 bg-gray-50 border-b border-gray-200">
          {isAdmin && (
            <button 
              onClick={onUploadClick}
              className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-medium py-3.5 px-4 rounded-xl flex items-center justify-center shadow-lg transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98]"
            >
              <span className="mr-2 text-lg">📤</span>
              <span className="font-medium">Upload Document</span>
            </button>
          )}
        </div>

        {/* Scrollable Content - Fixed */}
        <div className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden mobile-scroll-container" style={{ 
          maxHeight: 'calc(100vh - 140px)',
          WebkitOverflowScrolling: 'touch'
        }}>
          {/* Main Navigation */}
          <div className="p-3">
            <div className="space-y-1">
              {menuItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => onViewChange(item.id)}
                  className={`w-full flex items-center justify-between p-3 rounded-xl text-left transition-all duration-200 ${
                    selectedView === item.id
                      ? 'bg-gradient-to-r from-blue-50 to-indigo-50 text-blue-700 border border-blue-200 shadow-sm'
                      : 'text-gray-700 hover:bg-gray-50 active:bg-gray-100'
                  }`}
                  title={item.description}
                >
                  <div className="flex items-center space-x-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                      selectedView === item.id ? 'bg-blue-100' : 'bg-gray-100'
                    }`}>
                      <span className="text-lg">{item.icon}</span>
                    </div>
                    <span className="font-medium">{item.label}</span>
                  </div>
                  {item.count > 0 && (
                    <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                      selectedView === item.id
                        ? 'bg-blue-200 text-blue-800'
                        : 'bg-gray-200 text-gray-600'
                    }`}>
                      {item.count}
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Categories Section */}
          <div className="p-3 pt-0">
            <div className="flex items-center space-x-2 mb-3 px-1">
              <div className="w-1 h-4 bg-gradient-to-b from-blue-500 to-purple-500 rounded-full"></div>
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
                Categories
              </h3>
            </div>
            <div className="space-y-1">
              {categories.map((category) => (
                <button
                  key={category.id}
                  onClick={() => onViewChange(`category:${category.id}`)}
                  className={`w-full flex items-center space-x-3 p-3 rounded-xl text-left transition-all duration-200 ${
                    selectedView === `category:${category.id}`
                      ? 'bg-gradient-to-r from-blue-50 to-indigo-50 text-blue-700 border border-blue-200 shadow-sm'
                      : 'text-gray-700 hover:bg-gray-50 active:bg-gray-100'
                  }`}
                >
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                    selectedView === `category:${category.id}` ? 'bg-blue-100' : 'bg-gray-100'
                  }`}>
                    <span className={`text-lg ${category.color}`}>{category.icon}</span>
                  </div>
                  <span className="font-medium">{category.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Storage Usage */}
          <div className="p-4 m-3 bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl border border-gray-200">
            <div className="flex items-center space-x-2 mb-3">
              <div className="w-6 h-6 bg-blue-100 rounded-lg flex items-center justify-center">
                <span className="text-sm">💾</span>
              </div>
              <h4 className="text-sm font-semibold text-gray-700">Storage</h4>
            </div>
            <div className="space-y-2">
              <div className="bg-gray-200 rounded-full h-2 overflow-hidden">
                <div className="bg-gradient-to-r from-blue-500 to-blue-600 h-full rounded-full transition-all duration-300" style={{ width: '68%' }}></div>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-600 font-medium">6.8 GB used</span>
                <span className="text-xs text-gray-500">of 10 GB</span>
              </div>
            </div>
          </div>

          {/* Additional Test Content - To verify scrolling works */}
          <div className="p-3">
            <div className="space-y-2">
              <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                <h4 className="text-sm font-semibold text-blue-700 mb-1">Quick Actions</h4>
                <p className="text-xs text-blue-600">Access frequently used features</p>
              </div>
              <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                <h4 className="text-sm font-semibold text-green-700 mb-1">Recent Activity</h4>
                <p className="text-xs text-green-600">View your latest document interactions</p>
              </div>
              <div className="p-3 bg-purple-50 rounded-lg border border-purple-200">
                <h4 className="text-sm font-semibold text-purple-700 mb-1">Help & Support</h4>
                <p className="text-xs text-purple-600">Get assistance with the portal</p>
              </div>
            </div>
          </div>

          {/* Bottom Padding for Scrolling */}
          <div className="h-8"></div>
        </div>
      </div>
    );
  }

  // Desktop version (unchanged)
  return (
    <div className="w-64 h-full bg-white border-r border-gray-200 flex flex-col overflow-hidden">
      {/* Compose Button */}
      <div className="p-4 flex-shrink-0">
        {isAdmin && (
          <button 
            onClick={onUploadClick}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-2xl flex items-center justify-center shadow-md transition-colors touch-manipulation"
          >
            <span className="mr-2">✏️</span>
            Upload Document
          </button>
        )}
      </div>

      {/* Main Navigation - Scrollable Content */}
      <div className="flex-1 overflow-y-auto min-h-0">
        <nav className="px-2">
          {menuItems.map((item) => (
            <button
              key={item.id}
              onClick={() => onViewChange(item.id)}
              className={`w-full flex items-center justify-between px-4 py-3 rounded-lg mb-1 text-left transition-colors touch-manipulation ${
                selectedView === item.id
                  ? 'bg-blue-100 text-blue-800 font-medium'
                  : 'text-gray-700 hover:bg-gray-100 active:bg-gray-200'
              }`}
              title={item.description}
            >
              <div className="flex items-center">
                <span className="mr-3 text-lg">{item.icon}</span>
                <span className="text-sm">{item.label}</span>
              </div>
              {item.count > 0 && (
                <span className={`text-xs px-2 py-1 rounded-full ${
                  selectedView === item.id
                    ? 'bg-blue-200 text-blue-800'
                    : 'bg-gray-200 text-gray-600'
                }`}>
                  {item.count}
                </span>
              )}
            </button>
          ))}
        </nav>

        {/* Categories Section */}
        <div className="mt-6 px-2">
          <h3 className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
            Categories
          </h3>
          {categories.map((category) => (
            <button
              key={category.id}
              onClick={() => onViewChange(`category:${category.id}`)}
              className={`w-full flex items-center px-4 py-2 rounded-lg mb-1 text-left transition-colors touch-manipulation ${
                selectedView === `category:${category.id}`
                  ? 'bg-blue-100 text-blue-800 font-medium'
                  : 'text-gray-700 hover:bg-gray-100 active:bg-gray-200'
              }`}
            >
              <span className={`mr-3 text-lg ${category.color}`}>{category.icon}</span>
              <span className="text-sm">{category.label}</span>
            </button>
          ))}
        </div>

        {/* Storage Usage */}
        <div className="mt-6 px-6 pb-6">
          <div className="text-xs text-gray-500 mb-2">Storage</div>
          <div className="bg-gray-200 rounded-full h-2 mb-1">
            <div className="bg-blue-600 h-2 rounded-full" style={{ width: '68%' }}></div>
          </div>
          <div className="text-xs text-gray-500">
            6.8 GB of 10 GB used
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar; 