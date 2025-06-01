import React, { useState, useRef, useEffect } from 'react';
import { apiService } from '../services/api';
import LoadingSpinner from './LoadingSpinner';

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

interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
}

const DocumentUpload: React.FC<DocumentUploadProps> = ({
  isOpen,
  onClose,
  onUploadSuccess
}) => {
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
  const [users, setUsers] = useState<User[]>([]);
  const [isAdmin, setIsAdmin] = useState(false);
  const [userEmail, setUserEmail] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Check admin status and fetch data when modal opens
  useEffect(() => {
    if (isOpen) {
      const initializeComponent = async () => {
        // Check if user is admin
        const adminStatus = await apiService.isAdmin();
        setIsAdmin(adminStatus);
        
        if (!adminStatus) {
          // If not admin, close the modal and show error
          onClose();
          return;
        }

        // Fetch categories
        const fetchedCategories = await apiService.getCategories();
        setCategories(fetchedCategories);
        
        // Fetch departments for sharing
        const fetchedDepartments = await apiService.getDepartments();
        setDepartments(fetchedDepartments);
        
        // Fetch users for sharing
        const fetchedUsers = await apiService.getUsers();
        setUsers(fetchedUsers);
        
        // Set first category as default if available
        if (fetchedCategories.length > 0 && !form.category) {
          setForm(prev => ({ ...prev, category: fetchedCategories[0].id }));
        }
      };
      
      initializeComponent();
    }
  }, [isOpen, form.category, onClose]);

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
      
      // Add department IDs
      form.shared_departments.forEach(deptId => {
        formData.append('shared_departments', deptId);
      });
      
      // Add user emails
      form.shared_user_emails.forEach(email => {
        formData.append('shared_user_emails', email);
      });
      
      // Use selected category or first available category
      const categoryId = form.category || (categories.length > 0 ? categories[0].id : '');
      if (categoryId) {
        formData.append('category', categoryId);
      }

      // Call the API service
      await apiService.uploadDocument(formData);
      
      // Reset form
      setForm({
        title: '',
        description: '',
        category: categories.length > 0 ? categories[0].id : '',
        file: null,
        priority: 'medium',
        status: 'draft',
        visibility: 'private',
        shared_departments: [],
        shared_user_emails: [],
        allow_download: true,
        allow_reshare: false
      });
      onUploadSuccess();
      onClose();
    } catch (error) {
      console.error('Upload error:', error);
      // Error message is handled by the API service
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

  // Don't render if user is not admin
  if (!isAdmin && isOpen) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6">
          <div className="text-center">
            <div className="text-6xl mb-4">🚫</div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Access Denied</h2>
            <p className="text-gray-600 mb-4">Only administrators can upload documents.</p>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!isOpen) return null;

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
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
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
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
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
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
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
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
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
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
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
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="private">Private (Admin Only)</option>
              <option value="department">Share with Departments</option>
              <option value="users">Share with Specific Users</option>
              <option value="public">Public (Everyone)</option>
            </select>
          </div>

          {/* Shared Departments - Show only if department visibility selected */}
          {form.visibility === 'department' && (
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

          {/* Shared User Emails - Show only if users visibility selected */}
          {form.visibility === 'users' && (
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

          {/* Permission Settings - Show for department, users, and public */}
          {form.visibility !== 'private' && (
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