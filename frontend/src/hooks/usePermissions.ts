import { useState, useEffect } from 'react';
import { apiService } from '../services/api';

interface PermissionState {
  permissions: string[];
  isAdmin: boolean;
  isLoading: boolean;
  hasPermission: (permission: string) => boolean;
  refreshPermissions: () => Promise<void>;
}

export const usePermissions = (): PermissionState => {
  const [permissions, setPermissions] = useState<string[]>([]);
  const [isAdmin, setIsAdmin] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const loadPermissions = async () => {
    setIsLoading(true);
    try {
      const [adminStatus, userPermissions] = await Promise.all([
        apiService.isAdmin(),
        apiService.getUserPermissions()
      ]);
      
      setIsAdmin(adminStatus);
      setPermissions(userPermissions);
    } catch (error) {
      console.error('Error loading permissions:', error);
      setIsAdmin(false);
      setPermissions([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadPermissions();
  }, []);

  const hasPermission = (permission: string): boolean => {
    if (isAdmin) return true;
    return permissions.includes(permission);
  };

  const refreshPermissions = async () => {
    await loadPermissions();
  };

  return {
    permissions,
    isAdmin,
    isLoading,
    hasPermission,
    refreshPermissions
  };
}; 