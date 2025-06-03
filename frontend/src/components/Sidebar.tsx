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
    drafts: number;
  };
}

interface Category {
  id: string;
  name: string;
  description?: string;
  is_public: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({ 
  selectedView, 
  onViewChange, 
  onUploadClick,
  isMobile = false,
  documentCounts = { all: 0, important: 0, recent: 0, shared: 0, starred: 0, drafts: 0 }
}) => {
  const [isAdmin, setIsAdmin] = useState(false);
  const [canUpload, setCanUpload] = useState(false);
  const [categories, setCategories] = useState<Category[]>([]);
  const [isLoadingCategories, setIsLoadingCategories] = useState(false);

  // Check permissions when component mounts
  useEffect(() => {
    const checkPermissions = async () => {
      try {
        const adminStatus = await apiService.isAdmin();
        const uploadPermission = await apiService.hasPermission('documents.create');
        setIsAdmin(adminStatus);
        setCanUpload(adminStatus || uploadPermission);
      } catch (error) {
        console.error('Error checking permissions:', error);
        setIsAdmin(false);
        setCanUpload(false);
      }
    };

    checkPermissions();
  }, []);

  // Fetch categories from API
  useEffect(() => {
    const fetchCategories = async () => {
      setIsLoadingCategories(true);
      try {
        console.log('🔄 Fetching categories for sidebar...');
        const fetchedCategories = await apiService.getCategories();
        console.log('📂 Sidebar categories loaded:', fetchedCategories);
        setCategories(Array.isArray(fetchedCategories) ? fetchedCategories : []);
      } catch (error) {
        console.error('❌ Error fetching categories for sidebar:', error);
        setCategories([]);
      } finally {
        setIsLoadingCategories(false);
      }
    };

    fetchCategories();
  }, []);

  // Restructured navigation with logical grouping
  const navigationSections = [
    {
      title: "My Documents",
      items: [
        {
          id: 'all',
          label: 'All Documents',
          icon: '📄',
          count: documentCounts.all,
          description: 'View all available documents',
          isActive: true
        },
        {
          id: 'recent',
          label: 'Recently Viewed',
          icon: '🕒',
          count: documentCounts.recent,
          description: 'Documents you viewed in the last 7 days',
          isActive: true
        },
        {
          id: 'starred',
          label: 'Bookmarked',
          icon: '⭐',
          count: documentCounts.starred,
          description: 'Your bookmarked documents',
          isActive: true
        },
        {
          id: 'drafts',
          label: 'Draft Documents',
          icon: '📝',
          count: documentCounts.drafts,
          description: 'Documents in draft status',
          isActive: true
        }
      ]
    },
    {
      title: "Collaboration",
      items: [
        {
          id: 'shared',
          label: 'Shared With Me',
          icon: '👥',
          count: documentCounts.shared,
          description: 'Documents others have shared with you',
          isActive: true
        },
        {
          id: 'important',
          label: 'High Priority',
          icon: '🔴',
          count: documentCounts.important,
          description: 'Critical and high priority documents',
          isActive: true
        }
      ]
    }
  ];

  // Convert API categories to sidebar format
  const getCategoryIcon = (categoryName: string): string => {
    const name = categoryName.toLowerCase();
    if (name.includes('policy') || name.includes('policies')) return '📋';
    if (name.includes('report') || name.includes('analytics')) return '📊';
    if (name.includes('form') || name.includes('template')) return '📝';
    if (name.includes('manual') || name.includes('guide')) return '📚';
    if (name.includes('document') || name.includes('general')) return '📄';
    if (name.includes('finance') || name.includes('financial')) return '💰';
    if (name.includes('hr') || name.includes('human')) return '👥';
    if (name.includes('legal')) return '⚖️';
    if (name.includes('technical') || name.includes('tech')) return '🔧';
    if (name.includes('training')) return '🎓';
    return '📁'; // Default icon
  };

  const getCategoryColor = (categoryName: string): string => {
    const name = categoryName.toLowerCase();
    if (name.includes('policy') || name.includes('policies')) return 'text-blue-600';
    if (name.includes('report') || name.includes('analytics')) return 'text-green-600';
    if (name.includes('form') || name.includes('template')) return 'text-purple-600';
    if (name.includes('manual') || name.includes('guide')) return 'text-orange-600';
    if (name.includes('document') || name.includes('general')) return 'text-gray-600';
    if (name.includes('finance') || name.includes('financial')) return 'text-yellow-600';
    if (name.includes('hr') || name.includes('human')) return 'text-pink-600';
    if (name.includes('legal')) return 'text-indigo-600';
    if (name.includes('technical') || name.includes('tech')) return 'text-cyan-600';
    if (name.includes('training')) return 'text-emerald-600';
    return 'text-gray-600'; // Default color
  };

  const formatCategoriesForSidebar = (apiCategories: Category[]) => {
    return apiCategories.map(category => ({
      id: category.id,
      label: category.name,
      icon: getCategoryIcon(category.name),
      color: getCategoryColor(category.name),
      description: category.description || `Documents in the ${category.name} category`
    }));
  };

  // Helper function to render navigation item with active state indicator
  const renderNavItem = (item: any, isCategory = false) => {
    const itemId = isCategory ? `category:${item.id}` : item.id;
    const isActive = selectedView === itemId;
    
    return (
      <button
        key={item.id}
        onClick={() => onViewChange(itemId)}
        className={`w-full flex items-center justify-between p-3 rounded-xl text-left transition-all duration-200 group relative ${
          isActive
            ? 'bg-gradient-to-r from-blue-50 to-indigo-50 text-blue-700 border border-blue-200 shadow-sm'
            : 'text-gray-700 hover:bg-gray-50 active:bg-gray-100'
        }`}
        title={item.description}
        aria-label={item.description}
        aria-current={isActive ? 'page' : undefined}
      >
        {/* Active indicator */}
        {isActive && (
          <div className="absolute left-0 top-1/2 transform -translate-y-1/2 w-1 h-8 bg-blue-600 rounded-r-full"></div>
        )}
        
        <div className="flex items-center space-x-3">
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-200 ${
            isActive ? 'bg-blue-100' : 'bg-gray-100 group-hover:bg-gray-200'
          }`}>
            <span className={`text-lg ${isCategory ? item.color : ''}`}>{item.icon}</span>
          </div>
          <span className={`font-medium transition-colors duration-200 ${
            isActive ? 'text-blue-700' : 'text-gray-700 group-hover:text-gray-900'
          }`}>
            {item.label}
          </span>
        </div>
        
        {/* Count badge for documents */}
        {item.count > 0 && (
          <span className={`text-xs px-2.5 py-1 rounded-full font-medium transition-all duration-200 ${
            isActive
              ? 'bg-blue-200 text-blue-800'
              : 'bg-gray-200 text-gray-600 group-hover:bg-gray-300'
          }`}>
            {item.count}
          </span>
        )}
      </button>
    );
  };

  if (isMobile) {
    return (
      <div className="w-full h-full bg-white flex flex-col relative" data-component="sidebar">
        {/* Mobile Header - Fixed positioning to eliminate white space */}
        <div className="flex-shrink-0 bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg relative">
          {/* Safe area handling for devices with notch */}
          <div className="pt-safe-top"></div>
          <div className="p-4">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-white bg-opacity-20 rounded-lg flex items-center justify-center">
                <span className="text-lg">📂</span>
              </div>
              <div>
                <h2 className="font-semibold text-lg">Department Portal</h2>
                <p className="text-blue-100 text-sm">Document Management System</p>
              </div>
            </div>
          </div>
        </div>

        {/* Primary Action Button */}
        <div className="flex-shrink-0 p-4 bg-gray-50 border-b border-gray-200">
          {canUpload && (
            <button 
              onClick={onUploadClick}
              data-action="upload"
              className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-medium py-3.5 px-4 rounded-xl flex items-center justify-center shadow-lg transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98]"
              aria-label="Upload a new document"
            >
              <span className="mr-2 text-lg">📤</span>
              <span className="font-medium">Upload Document</span>
            </button>
          )}
        </div>

        {/* Scrollable Navigation Content - Improved mobile styling */}
        <div className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden bg-white mobile-scroll-container" style={{ 
          maxHeight: 'calc(100vh - 140px)',
          WebkitOverflowScrolling: 'touch'
        }}>
          {/* Navigation Sections */}
          {navigationSections.map((section, sectionIndex) => (
            <div key={section.title} className="p-3">
              {/* Section Header */}
              <div className="flex items-center space-x-2 mb-3 px-1">
                <div className="w-1 h-4 bg-gradient-to-b from-blue-500 to-purple-500 rounded-full"></div>
                <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
                  {section.title}
                </h3>
              </div>
              
              {/* Section Items */}
              <div className="space-y-1">
                {section.items.map((item) => renderNavItem(item))}
              </div>
              
              {/* Add spacing between sections */}
              {sectionIndex < navigationSections.length - 1 && <div className="mt-4"></div>}
            </div>
          ))}

          {/* Document Categories Section */}
          <div className="p-3 pt-0">
            <div className="flex items-center space-x-2 mb-3 px-1">
              <div className="w-1 h-4 bg-gradient-to-b from-green-500 to-blue-500 rounded-full"></div>
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
                Document Categories
              </h3>
            </div>
            <div className="space-y-1">
              {formatCategoriesForSidebar(categories).map((category) => renderNavItem(category, true))}
            </div>
          </div>

          {/* Storage Usage Widget */}
          <div className="p-4 m-3 bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl border border-gray-200">
            <div className="flex items-center space-x-2 mb-3">
              <div className="w-6 h-6 bg-blue-100 rounded-lg flex items-center justify-center">
                <span className="text-sm">💾</span>
              </div>
              <h4 className="text-sm font-semibold text-gray-700">Storage Usage</h4>
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

          {/* Quick Help Section */}
          <div className="p-3">
            <div className="space-y-2">
              <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                <h4 className="text-sm font-semibold text-blue-700 mb-1">Need Help?</h4>
                <p className="text-xs text-blue-600">Access help guides and support resources</p>
              </div>
            </div>
          </div>

          {/* Bottom Padding for Scrolling - Increased for better mobile experience */}
          <div className="h-16 pb-safe-bottom"></div>
        </div>
      </div>
    );
  }

  // Desktop version with improved structure
  return (
    <div className="w-64 h-full bg-white border-r border-gray-200 flex flex-col overflow-hidden" data-component="sidebar">
      {/* Primary Action Button */}
      <div className="p-4 flex-shrink-0">
        {canUpload && (
          <button 
            onClick={onUploadClick}
            data-action="upload"
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-2xl flex items-center justify-center shadow-md transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98]"
            aria-label="Upload a new document"
          >
            <span className="mr-2">📤</span>
            Upload Document
          </button>
        )}
      </div>

      {/* Navigation Content - Scrollable */}
      <div className="flex-1 overflow-y-auto min-h-0">
        {/* Navigation Sections */}
        {navigationSections.map((section, sectionIndex) => (
          <div key={section.title} className="px-2">
            {/* Section Header */}
            <h3 className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              {section.title}
            </h3>
            
            {/* Section Items */}
            <nav className="space-y-1 mb-4">
              {section.items.map((item) => renderNavItem(item))}
            </nav>
          </div>
        ))}

        {/* Document Categories Section */}
        <div className="px-2">
          <h3 className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
            Document Categories
          </h3>
          <nav className="space-y-1 mb-4">
            {formatCategoriesForSidebar(categories).map((category) => renderNavItem(category, true))}
          </nav>
        </div>

        {/* Storage Usage */}
        <div className="mt-6 px-6 pb-6">
          <div className="text-xs text-gray-500 mb-2 font-medium">Storage Usage</div>
          <div className="bg-gray-200 rounded-full h-2 mb-1">
            <div className="bg-blue-600 h-2 rounded-full transition-all duration-300" style={{ width: '68%' }}></div>
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