import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiService } from '../services/api';

interface UserPermissions {
  documents: {
    view_all: boolean;
    create: boolean;
    edit_all: boolean;
    delete_all: boolean;
    approve: boolean;
    share: boolean;
  };
  categories: {
    view_all: boolean;
    create: boolean;
    edit: boolean;
    delete: boolean;
    assign: boolean;
  };
  departments: {
    view_all: boolean;
    manage: boolean;
    assign_users: boolean;
    view_employees: boolean;
  };
  users: {
    view_all: boolean;
    create: boolean;
    edit: boolean;
    deactivate: boolean;
    assign_roles: boolean;
  };
  system: {
    admin_settings: boolean;
    view_analytics: boolean;
    manage_settings: boolean;
    backup: boolean;
  };
}

interface PermissionsContextType {
  permissions: UserPermissions | null;
  loading: boolean;
  error: string | null;
  isAdmin: boolean;
  refreshPermissions: () => Promise<void>;
  can: (permission: string) => boolean;
}

const PermissionsContext = createContext<PermissionsContextType | undefined>(undefined);

export const usePermissions = () => {
  const context = useContext(PermissionsContext);
  if (context === undefined) {
    throw new Error('usePermissions must be used within a PermissionsProvider');
  }
  return context;
};

interface PermissionsProviderProps {
  children: React.ReactNode;
}

export const PermissionsProvider: React.FC<PermissionsProviderProps> = ({ children }) => {
  const [permissions, setPermissions] = useState<UserPermissions | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);

  const refreshPermissions = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Check if user is admin first
      const adminStatus = await apiService.isAdmin();
      setIsAdmin(adminStatus);
      
      // Get permissions from API
      const response = await apiService.getCurrentUserPermissions();
      setPermissions(response.permissions);
      
      console.log('🔐 Permissions loaded:', {
        isAdmin: adminStatus,
        permissions: response.permissions
      });
    } catch (err: any) {
      console.error('Failed to fetch permissions:', err);
      setError(err.message || 'Failed to fetch permissions');
      setPermissions(null);
      setIsAdmin(false);
    } finally {
      setLoading(false);
    }
  };

  // Helper function to check permissions with dot notation
  const can = (permission: string): boolean => {
    // Admin users have all permissions automatically
    if (isAdmin) {
      console.log(`🔓 Admin access granted for: ${permission}`);
      return true;
    }
    
    if (!permissions) {
      console.log(`❌ No permissions loaded for: ${permission}`);
      return false;
    }
    
    const parts = permission.split('.');
    if (parts.length !== 2) {
      console.log(`❌ Invalid permission format: ${permission}`);
      return false;
    }
    
    const [category, action] = parts;
    const categoryPerms = permissions[category as keyof UserPermissions];
    
    if (!categoryPerms) {
      console.log(`❌ Category not found: ${category} for permission: ${permission}`);
      return false;
    }
    
    const hasPermission = (categoryPerms as any)[action] || false;
    console.log(`🔍 Permission check: ${permission} = ${hasPermission}`);
    return hasPermission;
  };

  useEffect(() => {
    // Only fetch permissions if user is authenticated
    const token = localStorage.getItem('access_token');
    if (token) {
      refreshPermissions();
    } else {
      setLoading(false);
    }
  }, []);

  const value: PermissionsContextType = {
    permissions,
    loading,
    error,
    isAdmin,
    refreshPermissions,
    can,
  };

  return (
    <PermissionsContext.Provider value={value}>
      {children}
    </PermissionsContext.Provider>
  );
};

// Helper hook for conditional rendering
export const useCanAccess = (permission: string) => {
  const { can } = usePermissions();
  return can(permission);
};

// Higher-order component for protecting components
export const withPermission = <P extends object>(
  WrappedComponent: React.ComponentType<P>,
  permission: string,
  fallback?: React.ComponentType<P> | null
) => {
  return (props: P) => {
    const { can } = usePermissions();
    
    if (can(permission)) {
      return <WrappedComponent {...props} />;
    }
    
    if (fallback) {
      const FallbackComponent = fallback;
      return <FallbackComponent {...props} />;
    }
    
    return null;
  };
}; 