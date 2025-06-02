import axios from 'axios';
import type { AxiosInstance, AxiosResponse } from 'axios';
import toast from 'react-hot-toast';

// Types
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: string;
  is_active: boolean;
  is_verified: boolean;
  profile?: UserProfile;
}

export interface UserProfile {
  employee_id?: string;
  phone_number?: string;
  avatar?: string;
  bio?: string;
  position?: string;
  department?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

export interface Document {
  id: string;
  title: string;
  description?: string;
  category_name: string;
  created_by_name: string;
  status: string;
  priority: string;
  file_type: string;
  file_size_mb: number;
  version: string;
  created_at: string;
  updated_at: string;
}

export interface SearchResult {
  document: Document;
  score: number;
  snippet: string;
  metadata: Record<string, any>;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total_found: number;
}

export interface DocumentStats {
  total_documents: number;
  published_documents: number;
  draft_documents: number;
  pending_review: number;
  vector_db_stats: {
    total_points: number;
    vector_size: number;
    distance_metric: string;
    status: string;
  };
}

class ApiService {
  private api: AxiosInstance;
  private baseURL: string;

  constructor() {
    this.baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
    
    this.api = axios.create({
      baseURL: this.baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.api.interceptors.request.use(
      (config) => {
        const token = this.getAccessToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor to handle token refresh
    this.api.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const refreshToken = this.getRefreshToken();
            if (refreshToken) {
              const response = await axios.post(`${this.baseURL}/accounts/auth/refresh/`, {
                refresh: refreshToken,
              });

              const { access } = response.data;
              this.setAccessToken(access);

              originalRequest.headers.Authorization = `Bearer ${access}`;
              return this.api(originalRequest);
            }
          } catch (refreshError) {
            this.logout();
            window.location.href = '/login';
          }
        }

        return Promise.reject(error);
      }
    );
  }

  // Token management
  private getAccessToken(): string | null {
    return localStorage.getItem('access_token');
  }

  private getRefreshToken(): string | null {
    return localStorage.getItem('refresh_token');
  }

  private setAccessToken(token: string): void {
    localStorage.setItem('access_token', token);
  }

  private setRefreshToken(token: string): void {
    localStorage.setItem('refresh_token', token);
  }

  private setTokens(access: string, refresh: string): void {
    this.setAccessToken(access);
    this.setRefreshToken(refresh);
  }

  // Authentication methods
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    try {
      const response: AxiosResponse<LoginResponse> = await this.api.post(
        '/accounts/auth/login/',
        credentials
      );

      const { access, refresh } = response.data;
      this.setTokens(access, refresh);

      toast.success('Login successful!');
      return response.data;
    } catch (error: any) {
      const message = error.response?.data?.error || 'Login failed';
      toast.error(message);
      throw error;
    }
  }

  async register(userData: any): Promise<LoginResponse> {
    try {
      const response: AxiosResponse<LoginResponse> = await this.api.post(
        '/accounts/auth/register/',
        userData
      );

      const { access, refresh } = response.data;
      this.setTokens(access, refresh);

      toast.success('Registration successful!');
      return response.data;
    } catch (error: any) {
      const message = error.response?.data?.error || 'Registration failed';
      toast.error(message);
      throw error;
    }
  }

  async logout(): Promise<void> {
    try {
      const refreshToken = this.getRefreshToken();
      if (refreshToken) {
        await this.api.post('/accounts/auth/logout/', {
          refresh: refreshToken,
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      toast.success('Logged out successfully');
    }
  }

  // Check if user is authenticated
  isAuthenticated(): boolean {
    return !!this.getAccessToken();
  }

  // Get current user profile
  async getCurrentUser(): Promise<User> {
    try {
      const response: AxiosResponse<User> = await this.api.get('/accounts/profile/');
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  // Check if current user is admin
  async isAdmin(): Promise<boolean> {
    try {
      const user = await this.getCurrentUser();
      return user.role === 'admin';
    } catch (error) {
      return false;
    }
  }

  // Get user role
  async getUserRole(): Promise<string> {
    try {
      const user = await this.getCurrentUser();
      return user.role;
    } catch (error) {
      return 'employee';
    }
  }

  // Get all departments for sharing options
  async getDepartments(): Promise<any[]> {
    try {
      const response = await this.api.get('/departments/');
      return response.data.results || response.data;
    } catch (error) {
      console.error('Failed to fetch departments:', error);
      return [];
    }
  }

  // Get all users for sharing options (admin only)
  async getUsers(): Promise<any[]> {
    try {
      const response = await this.api.get('/accounts/users/');
      return response.data.results || response.data;
    } catch (error) {
      console.error('Failed to fetch users:', error);
      return [];
    }
  }

  // Document search methods
  async searchDocuments(
    query: string,
    limit: number = 10,
    department?: string
  ): Promise<SearchResponse> {
    try {
      const params = new URLSearchParams({
        q: query,
        limit: limit.toString(),
      });

      if (department) {
        params.append('department', department);
      }

      const response: AxiosResponse<SearchResponse> = await this.api.get(
        `/documents/search/?${params.toString()}`
      );

      return response.data;
    } catch (error: any) {
      const message = error.response?.data?.error || 'Search failed';
      toast.error(message);
      throw error;
    }
  }

  // AI Chat methods
  async askQuestion(question: string): Promise<any> {
    try {
      const response = await this.api.post('/documents/chat/', {
        question: question
      });

      return response.data;
    } catch (error: any) {
      const message = error.response?.data?.error || 'AI chat failed';
      toast.error(message);
      throw error;
    }
  }

  // Document management
  async getDocuments(): Promise<Document[]> {
    try {
      const response: AxiosResponse<{ results: Document[] }> = await this.api.get('/documents/');
      return response.data.results || response.data;
    } catch (error) {
      toast.error('Failed to fetch documents');
      throw error;
    }
  }

  async getDocument(id: string): Promise<Document> {
    try {
      const response: AxiosResponse<Document> = await this.api.get(`/documents/${id}/`);
      return response.data;
    } catch (error) {
      toast.error('Failed to fetch document');
      throw error;
    }
  }

  async downloadDocument(id: string): Promise<Blob> {
    try {
      const response: AxiosResponse<Blob> = await this.api.get(`/documents/${id}/download/`, {
        responseType: 'blob',
      });
      return response.data;
    } catch (error) {
      toast.error('Failed to download document');
      throw error;
    }
  }

  async viewDocument(id: string): Promise<void> {
    try {
      await this.api.post(`/documents/${id}/view/`);
    } catch (error) {
      console.error('Failed to record document view:', error);
    }
  }

  async previewDocument(id: string): Promise<void> {
    try {
      // First, let's try to get the document details to verify access
      const documentData = await this.getDocument(id);
      
      // Record the view
      await this.viewDocument(id);
      
      // For mobile devices, use a different approach that doesn't rely on popups
      const isMobile = /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
      
      if (isMobile) {
        // Mobile-friendly approach: Create a temporary link and click it
        try {
          const response = await this.api.get(`/documents/${id}/preview/`, {
            responseType: 'blob',
          });
          
          // Create blob URL
          const blob = new Blob([response.data], { 
            type: response.headers['content-type'] || 'application/pdf' 
          });
          const url = window.URL.createObjectURL(blob);
          
          // Create a temporary link element and click it
          const link = window.document.createElement('a');
          link.href = url;
          link.target = '_blank';
          link.download = `${documentData.title || 'document'}.pdf`; // Provide a fallback filename
          link.rel = 'noopener noreferrer';
          
          // Add to DOM temporarily
          window.document.body.appendChild(link);
          
          // Trigger click
          link.click();
          
          // Clean up
          window.document.body.removeChild(link);
          setTimeout(() => {
            window.URL.revokeObjectURL(url);
          }, 100);
          
        } catch (previewError) {
          console.warn('Mobile preview failed, falling back to download:', previewError);
          // Fallback: Try the download approach
          await this.downloadDocumentMobile(id, documentData.title);
        }
      } else {
        // Desktop approach: Try to open in new tab
        try {
          const response = await this.api.get(`/documents/${id}/preview/`, {
            responseType: 'blob',
          });
          
          // Create blob URL and open in new tab
          const blob = new Blob([response.data], { type: response.headers['content-type'] || 'application/pdf' });
          const url = window.URL.createObjectURL(blob);
          const newWindow = window.open(url, '_blank');
          
          // Clean up the URL after a delay
          setTimeout(() => {
            window.URL.revokeObjectURL(url);
          }, 100);
          
          if (!newWindow) {
            toast.error('Please allow popups to preview documents');
          }
        } catch (previewError) {
          // Fallback: Try the download endpoint which we know works
          console.warn('Preview failed, falling back to download:', previewError);
          const blob = await this.downloadDocument(id);
          const url = window.URL.createObjectURL(blob);
          const newWindow = window.open(url, '_blank');
          
          setTimeout(() => {
            window.URL.revokeObjectURL(url);
          }, 100);
          
          if (!newWindow) {
            toast.error('Please allow popups to view documents');
          }
        }
      }
    } catch (error) {
      toast.error('Failed to preview document. Please try downloading it instead.');
      throw error;
    }
  }

  // Helper method for mobile downloads
  private async downloadDocumentMobile(id: string, title?: string): Promise<void> {
    try {
      const response = await this.api.get(`/documents/${id}/download/`, {
        responseType: 'blob',
      });
      
      const blob = new Blob([response.data], { 
        type: response.headers['content-type'] || 'application/octet-stream' 
      });
      const url = window.URL.createObjectURL(blob);
      
      // Create download link
      const link = window.document.createElement('a');
      link.href = url;
      link.download = title || 'document';
      link.style.display = 'none';
      
      // Add to DOM, click, and remove
      window.document.body.appendChild(link);
      link.click();
      window.document.body.removeChild(link);
      
      // Clean up
      setTimeout(() => {
        window.URL.revokeObjectURL(url);
      }, 100);
      
      toast.success('Document download started');
    } catch (error) {
      toast.error('Failed to download document');
      throw error;
    }
  }

  async updateDocumentPriority(id: string, priority: string): Promise<Document> {
    try {
      const response: AxiosResponse<Document> = await this.api.patch(`/documents/${id}/update/`, {
        priority: priority
      });
      return response.data;
    } catch (error) {
      toast.error('Failed to update document priority');
      throw error;
    }
  }

  async deleteDocument(id: string, showToast: boolean = true): Promise<void> {
    try {
      await this.api.delete(`/documents/${id}/delete/`);
      if (showToast) {
        toast.success('Document deleted successfully');
      }
    } catch (error) {
      if (showToast) {
        toast.error('Failed to delete document');
      }
      throw error;
    }
  }

  async deleteDocuments(ids: string[]): Promise<void> {
    try {
      // Delete documents one by one without individual toast messages
      await Promise.all(ids.map(id => this.deleteDocument(id, false)));
      toast.success(`${ids.length} document(s) deleted successfully`);
    } catch (error) {
      toast.error('Failed to delete documents');
      throw error;
    }
  }

  async uploadDocument(formData: FormData): Promise<Document> {
    try {
      const response: AxiosResponse<Document> = await this.api.post('/documents/create/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      toast.success('Document uploaded successfully!');
      return response.data;
    } catch (error: any) {
      const message = error.response?.data?.error || 'Failed to upload document';
      toast.error(message);
      throw error;
    }
  }

  async getCategories(): Promise<any[]> {
    try {
      const response = await this.api.get('/documents/categories/');
      return response.data.results || response.data;
    } catch (error) {
      console.error('Failed to fetch categories:', error);
      return [];
    }
  }

  // Statistics
  async getDocumentStats(): Promise<DocumentStats> {
    try {
      const response: AxiosResponse<DocumentStats> = await this.api.get('/documents/stats/');
      return response.data;
    } catch (error) {
      toast.error('Failed to fetch statistics');
      throw error;
    }
  }

  // Health check
  async healthCheck(): Promise<{ status: string; message: string }> {
    try {
      const response = await axios.get(`${this.baseURL.replace('/api/v1', '')}/health/`);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  // Group management
  async getGroups(): Promise<any[]> {
    try {
      const response = await this.api.get('/accounts/groups/');
      return response.data.results || response.data;
    } catch (error) {
      console.error('Failed to fetch groups:', error);
      return [];
    }
  }

  async getGroup(id: string): Promise<any> {
    try {
      const response = await this.api.get(`/accounts/groups/${id}/`);
      return response.data;
    } catch (error) {
      toast.error('Failed to fetch group details');
      throw error;
    }
  }

  async createGroup(groupData: any): Promise<any> {
    try {
      const response = await this.api.post('/accounts/groups/create/', groupData);
      toast.success('Group created successfully!');
      return response.data;
    } catch (error: any) {
      const message = error.response?.data?.error || 'Failed to create group';
      toast.error(message);
      throw error;
    }
  }

  async updateGroup(id: string, groupData: any): Promise<any> {
    try {
      const response = await this.api.patch(`/accounts/groups/${id}/update/`, groupData);
      toast.success('Group updated successfully!');
      return response.data;
    } catch (error: any) {
      const message = error.response?.data?.error || 'Failed to update group';
      toast.error(message);
      throw error;
    }
  }

  async deleteGroup(id: string): Promise<void> {
    try {
      await this.api.delete(`/accounts/groups/${id}/delete/`);
      toast.success('Group deleted successfully');
    } catch (error: any) {
      const message = error.response?.data?.error || 'Failed to delete group';
      toast.error(message);
      throw error;
    }
  }

  async addUserToGroup(groupId: string, userId: string): Promise<any> {
    try {
      const response = await this.api.post(`/accounts/groups/${groupId}/add-user/`, {
        user_id: userId
      });
      toast.success('User added to group successfully!');
      return response.data;
    } catch (error: any) {
      const message = error.response?.data?.error || 'Failed to add user to group';
      toast.error(message);
      throw error;
    }
  }

  async removeUserFromGroup(groupId: string, userId: string): Promise<any> {
    try {
      const response = await this.api.delete(`/accounts/groups/${groupId}/remove-user/${userId}/`);
      toast.success('User removed from group successfully!');
      return response.data;
    } catch (error: any) {
      const message = error.response?.data?.error || 'Failed to remove user from group';
      toast.error(message);
      throw error;
    }
  }
}

// Export singleton instance
export const apiService = new ApiService();
export default apiService; 