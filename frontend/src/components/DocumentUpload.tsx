import React, { useState, useRef, useEffect } from 'react';
import { apiService } from '../services/api';
import LoadingSpinner from './LoadingSpinner';
import { usePermissions } from '../contexts/PermissionsContext';

interface DocumentUploadProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess: () => void;
}

interface UploadForm {
  title: string;
  description: string;
  category: string;
  file: File | null;
  priority: string;
  status: string;
  visibility: string;
  shared_departments: string[];
  shared_user_emails: string[];
  allow_download: boolean;
  allow_reshare: boolean;
}

interface Category {
  id: string;
  name: string;
}

interface Department {
  id: string;
  name: string;
}

const DocumentUpload: React.FC<DocumentUploadProps> = ({
  isOpen,
  onClose,
  onUploadSuccess
}) => {
  const { can } = usePermissions();
  const [form, setForm] = useState<UploadForm>({
    title: '',
    description: '',
    category: '',
    file: null,
    priority: 'medium',
    status: 'draft',
    visibility: 'private',
    shared_departments: [],
    shared_user_emails: [],
    allow_download: true,
    allow_reshare: false
  });
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [categories, setCategories] = useState<Category[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [userEmail, setUserEmail] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Permission checks
  const canCreateDocuments = can('documents.create');
  const canViewCategories = can('categories.view_all');
  const canShareDocuments = can('documents.share');

  // Check admin status and fetch data when modal opens
  useEffect(() => {
    if (isOpen && canCreateDocuments) {
      const initializeComponent = async () => {
        try {
          console.log('🔄 Refreshing categories and departments for document upload...');
          
          // Always fetch fresh categories if user can view them
          if (canViewCategories) {
            const fetchedCategories = await apiService.getCategories();
            console.log('📂 Fetched categories:', fetchedCategories);
            setCategories(Array.isArray(fetchedCategories) ? fetchedCategories : []);
            
            // Set first category as default if available and no category selected
            if (fetchedCategories.length > 0 && !form.category) {
              console.log('📋 Setting default category:', fetchedCategories[0].name);
              setForm(prev => ({ ...prev, category: fetchedCategories[0].id }));
            }
          }
          
          // Always fetch fresh departments for sharing if user can share
          if (canShareDocuments) {
            const fetchedDepartments = await apiService.getDepartments();
            console.log('🏢 Fetched departments:', fetchedDepartments);
            setDepartments(Array.isArray(fetchedDepartments) ? fetchedDepartments : []);
          }
        } catch (error) {
          console.error('❌ Error fetching categories/departments:', error);
          setCategories([]);
          setDepartments([]);
        }
      };
      
      initializeComponent();
    }
  }, [isOpen, canCreateDocuments, canViewCategories, canShareDocuments]); // Remove form.category dependency to always refresh

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    
    if (type === 'checkbox') {
      const checked = (e.target as HTMLInputElement).checked;
      setForm(prev => ({ ...prev, [name]: checked }));
    } else {
      setForm(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleArrayChange = (name: string, value: string, checked: boolean) => {
    setForm(prev => ({
      ...prev,
      [name]: checked 
        ? [...(prev[name as keyof UploadForm] as string[]), value]
        : (prev[name as keyof UploadForm] as string[]).filter(item => item !== value)
    }));
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    setForm(prev => ({ ...prev, file }));
    
    // Auto-fill title if empty
    if (file && !form.title) {
      const nameWithoutExtension = file.name.replace(/\.[^/.]+$/, "");
      setForm(prev => ({ ...prev, title: nameWithoutExtension }));
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setForm(prev => ({ ...prev, file }));
      
      // Auto-fill title if empty
      if (!form.title) {
        const nameWithoutExtension = file.name.replace(/\.[^/.]+$/, "");
        setForm(prev => ({ ...prev, title: nameWithoutExtension }));
      }
    }
  };

  const addUserEmail = () => {
    if (userEmail && !form.shared_user_emails.includes(userEmail)) {
      setForm(prev => ({
        ...prev,
        shared_user_emails: [...prev.shared_user_emails, userEmail]
      }));
      setUserEmail('');
    }
  };

  const removeUserEmail = (email: string) => {
    setForm(prev => ({
      ...prev,
      shared_user_emails: prev.shared_user_emails.filter(e => e !== email)
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canCreateDocuments) {
      return; // Prevent submission if user doesn't have permission
    }
    if (!form.file || !form.title) return;

    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append('title', form.title);
      formData.append('description', form.description);
      formData.append('file', form.file);
      formData.append('priority', form.priority);
      formData.append('status', form.status);
      formData.append('visibility', form.visibility);
      formData.append('allow_download', form.allow_download.toString());
      formData.append('allow_reshare', form.allow_reshare.toString());
      
      // Add department IDs (only if user can share)
      if (canShareDocuments) {
        form.shared_departments.forEach(deptId => {
          formData.append('shared_departments', deptId);
        });
        
        // Add user emails (only if user can share)
        form.shared_user_emails.forEach(email => {
          formData.append('shared_user_emails', email);
        });
      }
      
      // Use selected category or first available category
      const categoryId = form.category || (categories.length > 0 ? categories[0].id : '');
      if (categoryId) {
        formData.append('category', categoryId);
      }

      // Call the API service
      await apiService.uploadDocument(formData);
      
      resetForm();
      onUploadSuccess();
      onClose();
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setIsUploading(false);
    }
  };

  const resetForm = () => {
    setForm({
      title: '',
      description: '',
      category: '',
      file: null,
      priority: 'medium',
      status: 'draft',
      visibility: 'private',
      shared_departments: [],
      shared_user_emails: [],
      allow_download: true,
      allow_reshare: false
    });
    setUserEmail('');
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  // Don't render if modal should not be open
  if (!isOpen) {
    return null;
  }

  // Don't render if user doesn't have permission
  if (!canCreateDocuments) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Access Denied</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 p-2 rounded-lg hover:bg-gray-100"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <p className="text-gray-600 mb-4">
            You don't have permission to upload documents.
          </p>
          <button
            onClick={onClose}
            className="btn-primary w-full"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 rounded-t-xl">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-semibold text-gray-900">Upload Document</h2>
              <p className="text-sm text-gray-600 mt-1">Add a new document to the portal</p>
            </div>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-600 p-2 rounded-lg hover:bg-gray-100"
              disabled={isUploading}
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* File Upload Area */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Document File *
            </label>
            <div
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                dragActive
                  ? 'border-blue-500 bg-blue-50'
                  : form.file
                  ? 'border-green-500 bg-green-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              {form.file ? (
                <div className="space-y-2">
                  <div className="text-4xl">📄</div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{form.file.name}</p>
                    <p className="text-xs text-gray-500">
                      {(form.file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setForm(prev => ({ ...prev, file: null }))}
                    className="text-sm text-red-600 hover:text-red-700"
                  >
                    Remove file
                  </button>
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="text-4xl text-gray-400">📁</div>
                  <div>
                    <p className="text-sm text-gray-600">
                      Drag and drop your file here, or{' '}
                      <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        className="text-blue-600 hover:text-blue-700 font-medium"
                      >
                        browse
                      </button>
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      Supports: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, TXT (Max: 10MB)
                    </p>
                  </div>
                </div>
              )}
              <input
                ref={fileInputRef}
                type="file"
                onChange={handleFileChange}
                accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt"
                className="hidden"
              />
            </div>
          </div>

          {/* Title */}
          <div className="space-y-2">
            <label htmlFor="title" className="block text-sm font-medium text-gray-700">
              Document Title *
            </label>
            <input
              id="title"
              name="title"
              type="text"
              value={form.title}
              onChange={handleInputChange}
              placeholder="Enter document title"
              className="input-field"
              style={{ color: '#111827', backgroundColor: '#ffffff' }}
              required
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <label htmlFor="description" className="block text-sm font-medium text-gray-700">
              Description
            </label>
            <textarea
              id="description"
              name="description"
              value={form.description}
              onChange={handleInputChange}
              placeholder="Enter document description (optional)"
              rows={3}
              className="input-field resize-none"
              style={{ color: '#111827', backgroundColor: '#ffffff' }}
            />
          </div>

          {/* Category and Priority Row */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label htmlFor="category" className="block text-sm font-medium text-gray-700">
                Category
              </label>
              <select
                id="category"
                name="category"
                value={form.category}
                onChange={handleInputChange}
                className="input-field"
                style={{ color: '#111827', backgroundColor: '#ffffff' }}
              >
                <option value="">Select category</option>
                {categories.map(cat => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <label htmlFor="priority" className="block text-sm font-medium text-gray-700">
                Priority
              </label>
              <select
                id="priority"
                name="priority"
                value={form.priority}
                onChange={handleInputChange}
                className="input-field"
                style={{ color: '#111827', backgroundColor: '#ffffff' }}
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
          </div>

          {/* Status */}
          <div className="space-y-2">
            <label htmlFor="status" className="block text-sm font-medium text-gray-700">
              Status
            </label>
            <select
              id="status"
              name="status"
              value={form.status}
              onChange={handleInputChange}
              className="input-field"
              style={{ color: '#111827', backgroundColor: '#ffffff' }}
            >
              <option value="draft">Draft</option>
              <option value="review">Under Review</option>
              <option value="published">Published</option>
            </select>
          </div>

          {/* Visibility */}
          <div className="space-y-2">
            <label htmlFor="visibility" className="block text-sm font-medium text-gray-700">
              Who can see this document? *
            </label>
            <select
              id="visibility"
              name="visibility"
              value={form.visibility}
              onChange={handleInputChange}
              className="input-field"
              style={{ color: '#111827', backgroundColor: '#ffffff' }}
            >
              <option value="private">Private (Admin Only)</option>
              {canShareDocuments && <option value="department">Share with Departments</option>}
              {canShareDocuments && <option value="users">Share with Specific Users</option>}
              {canShareDocuments && <option value="public">Public (Everyone)</option>}
            </select>
          </div>

          {/* Shared Departments - Show only if department visibility selected and user can share */}
          {form.visibility === 'department' && canShareDocuments && (
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">
                Select Departments *
              </label>
              <div className="max-h-32 overflow-y-auto border border-gray-300 rounded-lg p-2">
                {departments.map(dept => (
                  <div key={dept.id} className="flex items-center space-x-2 p-1">
                    <input
                      type="checkbox"
                      id={`dept-${dept.id}`}
                      checked={form.shared_departments.includes(dept.id)}
                      onChange={(e) => handleArrayChange('shared_departments', dept.id, e.target.checked)}
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <label htmlFor={`dept-${dept.id}`} className="text-sm text-gray-700">
                      {dept.name}
                    </label>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Shared User Emails - Show only if users visibility selected and user can share */}
          {form.visibility === 'users' && canShareDocuments && (
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">
                Add User Emails *
              </label>
              <div className="flex space-x-2">
                <input
                  type="email"
                  value={userEmail}
                  onChange={(e) => setUserEmail(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addUserEmail())}
                  placeholder="Enter user email"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <button
                  type="button"
                  onClick={addUserEmail}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Add
                </button>
              </div>
              
              {/* Display added emails */}
              {form.shared_user_emails.length > 0 && (
                <div className="space-y-1">
                  <p className="text-sm text-gray-600">Added users:</p>
                  <div className="flex flex-wrap gap-2">
                    {form.shared_user_emails.map(email => (
                      <span
                        key={email}
                        className="inline-flex items-center px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full"
                      >
                        {email}
                        <button
                          type="button"
                          onClick={() => removeUserEmail(email)}
                          className="ml-2 text-blue-600 hover:text-blue-800"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Permission Settings - Show for department, users, and public only if user can share */}
          {form.visibility !== 'private' && canShareDocuments && (
            <div className="space-y-3 p-4 bg-gray-50 rounded-lg">
              <h4 className="text-sm font-medium text-gray-700">Permission Settings</h4>
              
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="allow_download"
                  name="allow_download"
                  checked={form.allow_download}
                  onChange={handleInputChange}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="allow_download" className="text-sm text-gray-700">
                  Allow download
                </label>
              </div>
              
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="allow_reshare"
                  name="allow_reshare"
                  checked={form.allow_reshare}
                  onChange={handleInputChange}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="allow_reshare" className="text-sm text-gray-700">
                  Allow recipients to reshare
                </label>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              disabled={isUploading}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!form.file || !form.title || isUploading}
              className="px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {isUploading ? (
                <>
                  <LoadingSpinner />
                  <span className="ml-2">Uploading...</span>
                </>
              ) : (
                <>
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  Upload Document
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default DocumentUpload; 