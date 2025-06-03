import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import LoadingSpinner from './LoadingSpinner';
import toast from 'react-hot-toast';

// Category Management Component
const CategoryManagement: React.FC = () => {
  const [categories, setCategories] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingCategory, setEditingCategory] = useState<any>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    parent_category: '',
    color: '#3B82F6'
  });

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const data = await apiService.getCategories();
      setCategories(data);
    } catch (error) {
      console.error('Failed to load categories:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingCategory) {
        await apiService.updateCategory(editingCategory.id, formData);
      } else {
        await apiService.createCategory(formData);
      }
      
      setFormData({ name: '', description: '', parent_category: '', color: '#3B82F6' });
      setEditingCategory(null);
      setShowModal(false);
      loadCategories();
    } catch (error) {
      console.error('Failed to save category:', error);
    }
  };

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this category?')) {
      try {
        await apiService.deleteCategory(id);
        loadCategories();
      } catch (error) {
        console.error('Failed to delete category:', error);
      }
    }
  };

  const handleEdit = (category: any) => {
    setEditingCategory(category);
    setFormData({
      name: category.name,
      description: category.description || '',
      parent_category: category.parent_category?.id || '',
      color: category.color || '#3B82F6'
    });
    setShowModal(true);
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex-shrink-0 flex justify-between items-center mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Category Management</h3>
          <p className="text-sm text-gray-600 mt-1">Organize documents with categories</p>
        </div>
        <button
          onClick={() => {
            setEditingCategory(null);
            setFormData({ name: '', description: '', parent_category: '', color: '#3B82F6' });
            setShowModal(true);
          }}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors flex items-center"
        >
          <span className="mr-2">➕</span>
          Add Category
        </button>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 min-h-0">
        <div className="h-full overflow-y-auto">
          <div className="bg-white rounded-lg border border-gray-200">
            {categories.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-gray-400 text-4xl mb-4">📁</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No categories yet</h3>
                <p className="text-gray-500 mb-4">Get started by creating your first document category</p>
                <button
                  onClick={() => {
                    setEditingCategory(null);
                    setFormData({ name: '', description: '', parent_category: '', color: '#3B82F6' });
                    setShowModal(true);
                  }}
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
                >
                  Create Category
                </button>
              </div>
            ) : (
              <div className="divide-y divide-gray-200">
                {categories.map((category) => (
                  <div key={category.id} className="p-6 hover:bg-gray-50 transition-colors">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div 
                          className="w-4 h-4 rounded-full"
                          style={{ backgroundColor: category.color || '#3B82F6' }}
                        ></div>
                        <div>
                          <h4 className="text-sm font-medium text-gray-900">{category.name}</h4>
                          {category.description && (
                            <p className="text-sm text-gray-500 mt-1">{category.description}</p>
                          )}
                          {category.parent_category && (
                            <p className="text-xs text-gray-400 mt-1">
                              Parent: {category.parent_category.name}
                            </p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs text-gray-500">
                          {category.document_count || 0} documents
                        </span>
                        <button
                          onClick={() => handleEdit(category)}
                          className="text-blue-600 hover:text-blue-800 text-sm"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDelete(category.id)}
                          className="text-red-600 hover:text-red-800 text-sm"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">
              {editingCategory ? 'Edit Category' : 'Create Category'}
            </h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category Name *
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter category name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                  placeholder="Enter category description"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Parent Category
                </label>
                <select
                  value={formData.parent_category}
                  onChange={(e) => setFormData({ ...formData, parent_category: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">No parent (root category)</option>
                  {categories
                    .filter(cat => !editingCategory || cat.id !== editingCategory.id)
                    .map(cat => (
                      <option key={cat.id} value={cat.id}>{cat.name}</option>
                    ))
                  }
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Color
                </label>
                <input
                  type="color"
                  value={formData.color}
                  onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                  className="w-full h-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex-1 bg-gray-200 text-gray-800 px-4 py-2 rounded-md hover:bg-gray-300 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
                >
                  {editingCategory ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

// Department Management Component
const DepartmentManagement: React.FC = () => {
  const [departments, setDepartments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingDepartment, setEditingDepartment] = useState<any>(null);
  const [formData, setFormData] = useState({
    name: '',
    code: '',
    description: '',
    email: '',
    phone: '',
    location: '',
    is_active: true
  });
  
  // Employee management state
  const [availableEmployees, setAvailableEmployees] = useState<any[]>([]);
  const [currentEmployees, setCurrentEmployees] = useState<any[]>([]);
  const [loadingEmployees, setLoadingEmployees] = useState(false);
  const [showEmployeeSection, setShowEmployeeSection] = useState(false);

  useEffect(() => {
    loadDepartments();
  }, []);

  // Load available employees when modal opens for editing
  useEffect(() => {
    if (editingDepartment && showCreateModal) {
      loadEmployeeData();
    }
  }, [editingDepartment, showCreateModal]);

  const loadDepartments = async () => {
    try {
      const data = await apiService.getDepartments();
      setDepartments(data);
    } catch (error) {
      toast.error('Failed to load departments');
    } finally {
      setLoading(false);
    }
  };

  const loadEmployeeData = async () => {
    if (!editingDepartment) return;
    
    setLoadingEmployees(true);
    try {
      const [available, current] = await Promise.all([
        apiService.getAvailableEmployees(),
        apiService.getDepartmentEmployees(editingDepartment.id)
      ]);
      
      console.log('📋 Available employees:', available);
      console.log('👥 Current employees:', current);
      
      setAvailableEmployees(available);
      setCurrentEmployees(current);
    } catch (error) {
      console.error('Error loading employee data:', error);
      toast.error('Failed to load employee data');
    } finally {
      setLoadingEmployees(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingDepartment) {
        // Update department
        await apiService.updateDepartment(editingDepartment.id, formData);
      } else {
        // Create department
        await apiService.createDepartment(formData);
      }
      setShowCreateModal(false);
      setEditingDepartment(null);
      setFormData({ name: '', code: '', description: '', email: '', phone: '', location: '', is_active: true });
      setShowEmployeeSection(false);
      setCurrentEmployees([]);
      setAvailableEmployees([]);
      loadDepartments();
    } catch (error) {
      console.error('Error saving department:', error);
    }
  };

  const handleDelete = async (id: string) => {
    if (confirm('Are you sure you want to delete this department?')) {
      try {
        await apiService.deleteDepartment(id);
        loadDepartments();
      } catch (error) {
        console.error('Error deleting department:', error);
      }
    }
  };

  const handleAssignEmployee = async (employeeId: string) => {
    if (!editingDepartment) return;
    
    try {
      await apiService.assignEmployeeToDepartment({
        employee: employeeId,
        department: editingDepartment.id,
        is_primary: true
      });
      
      // Refresh employee data
      await loadEmployeeData();
    } catch (error) {
      console.error('Error assigning employee:', error);
    }
  };

  const handleRemoveEmployee = async (assignmentId: string) => {
    if (confirm('Are you sure you want to remove this employee from the department?')) {
      try {
        await apiService.endEmployeeAssignment(assignmentId);
        
        // Refresh employee data
        await loadEmployeeData();
      } catch (error) {
        console.error('Error removing employee:', error);
      }
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900">Departments</h3>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn-primary"
        >
          Add Department
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {departments.map((dept) => (
          <div key={dept.id} className="bg-white shadow rounded-lg p-6">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h4 className="text-lg font-semibold text-gray-900">{dept.name}</h4>
                <p className="text-sm text-gray-500">Code: {dept.code}</p>
              </div>
              <span className={`inline-flex px-2 py-1 text-xs rounded-full ${
                dept.is_active 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-red-100 text-red-800'
              }`}>
                {dept.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
            {dept.description && (
              <p className="text-sm text-gray-600 mb-3">{dept.description}</p>
            )}
            <div className="space-y-1 text-sm text-gray-500">
              {dept.email && <p>📧 {dept.email}</p>}
              {dept.location && <p>📍 {dept.location}</p>}
              {dept.employees_count !== undefined && <p>👥 {dept.employees_count} employees</p>}
            </div>
            <div className="mt-4 flex space-x-2">
              <button
                onClick={() => {
                  setEditingDepartment(dept);
                  setFormData({
                    name: dept.name,
                    code: dept.code,
                    description: dept.description || '',
                    email: dept.email || '',
                    phone: dept.phone || '',
                    location: dept.location || '',
                    is_active: dept.is_active
                  });
                  setShowCreateModal(true);
                }}
                className="text-blue-600 hover:text-blue-900 text-sm"
              >
                Edit
              </button>
              <button
                onClick={() => handleDelete(dept.id)}
                className="text-red-600 hover:text-red-900 text-sm"
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Create/Edit Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">
              {editingDepartment ? 'Edit Department' : 'Create Department'}
            </h3>
            
            {/* Tab Navigation for Edit Mode */}
            {editingDepartment && (
              <div className="flex border-b border-gray-200 mb-6">
                <button
                  onClick={() => setShowEmployeeSection(false)}
                  className={`py-2 px-4 font-medium text-sm border-b-2 transition-colors ${
                    !showEmployeeSection
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Department Details
                </button>
                <button
                  onClick={() => setShowEmployeeSection(true)}
                  className={`py-2 px-4 font-medium text-sm border-b-2 transition-colors ${
                    showEmployeeSection
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Manage Employees ({currentEmployees.length})
                </button>
              </div>
            )}

            {/* Department Details Form */}
            {!showEmployeeSection && (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Name
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    className="input-field"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Code
                  </label>
                  <input
                    type="text"
                    value={formData.code}
                    onChange={(e) => setFormData(prev => ({ ...prev, code: e.target.value.toUpperCase() }))}
                    className="input-field"
                    maxLength={10}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                    className="input-field"
                    rows={2}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email
                  </label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                    className="input-field"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Location
                  </label>
                  <input
                    type="text"
                    value={formData.location}
                    onChange={(e) => setFormData(prev => ({ ...prev, location: e.target.value }))}
                    className="input-field"
                  />
                </div>
                <div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.is_active}
                      onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-700">Active Department</span>
                  </label>
                </div>
                <div className="flex space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={() => {
                      setShowCreateModal(false);
                      setEditingDepartment(null);
                      setShowEmployeeSection(false);
                      setFormData({ name: '', code: '', description: '', email: '', phone: '', location: '', is_active: true });
                    }}
                    className="btn-secondary flex-1"
                  >
                    Cancel
                  </button>
                  <button type="submit" className="btn-primary flex-1">
                    {editingDepartment ? 'Update' : 'Create'}
                  </button>
                </div>
              </form>
            )}

            {/* Employee Management Section */}
            {showEmployeeSection && editingDepartment && (
              <div className="space-y-6">
                {loadingEmployees ? (
                  <div className="flex items-center justify-center py-8">
                    <LoadingSpinner />
                  </div>
                ) : (
                  <>
                    {/* Current Employees */}
                    <div>
                      <h4 className="text-md font-semibold text-gray-900 mb-3">
                        Current Employees ({currentEmployees.length})
                      </h4>
                      {currentEmployees.length === 0 ? (
                        <p className="text-gray-500 text-sm">No employees assigned to this department.</p>
                      ) : (
                        <div className="space-y-2 max-h-48 overflow-y-auto">
                          {currentEmployees.map((assignment) => (
                            <div key={assignment.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                              <div className="flex items-center space-x-3">
                                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                                  <span className="text-sm font-medium text-blue-600">
                                    {assignment.employee_name?.split(' ').map((n: string) => n[0]).join('') || '?'}
                                  </span>
                                </div>
                                <div>
                                  <p className="text-sm font-medium text-gray-900">{assignment.employee_name}</p>
                                  <p className="text-xs text-gray-500">{assignment.employee_email}</p>
                                  {assignment.position_title && (
                                    <p className="text-xs text-blue-600">{assignment.position_title}</p>
                                  )}
                                </div>
                              </div>
                              <div className="flex items-center space-x-2">
                                {assignment.is_primary && (
                                  <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">Primary</span>
                                )}
                                <button
                                  onClick={() => handleRemoveEmployee(assignment.id)}
                                  className="text-red-600 hover:text-red-800 text-xs"
                                >
                                  Remove
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Available Employees */}
                    <div>
                      <h4 className="text-md font-semibold text-gray-900 mb-3">
                        Available Employees ({availableEmployees.length})
                      </h4>
                      {availableEmployees.length === 0 ? (
                        <p className="text-gray-500 text-sm">No employees available for assignment.</p>
                      ) : (
                        <div className="space-y-2 max-h-48 overflow-y-auto">
                          {availableEmployees.map((employee) => (
                            <div key={employee.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                              <div className="flex items-center space-x-3">
                                <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
                                  <span className="text-sm font-medium text-gray-600">
                                    {employee.name?.split(' ').map((n: string) => n[0]).join('') || employee.email[0].toUpperCase()}
                                  </span>
                                </div>
                                <div>
                                  <p className="text-sm font-medium text-gray-900">{employee.name || employee.email}</p>
                                  <p className="text-xs text-gray-500">{employee.email}</p>
                                  <span className={`text-xs px-2 py-1 rounded ${
                                    employee.role === 'admin' 
                                      ? 'bg-purple-100 text-purple-700' 
                                      : 'bg-blue-100 text-blue-700'
                                  }`}>
                                    {employee.role}
                                  </span>
                                </div>
                              </div>
                              <button
                                onClick={() => handleAssignEmployee(employee.id)}
                                className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                              >
                                Assign
                              </button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Action Buttons */}
                    <div className="flex space-x-3 pt-4 border-t">
                      <button
                        type="button"
                        onClick={() => {
                          setShowCreateModal(false);
                          setEditingDepartment(null);
                          setShowEmployeeSection(false);
                          setFormData({ name: '', code: '', description: '', email: '', phone: '', location: '', is_active: true });
                        }}
                        className="btn-secondary flex-1"
                      >
                        Close
                      </button>
                      <button
                        onClick={() => loadEmployeeData()}
                        className="btn-primary flex-1"
                      >
                        Refresh Data
                      </button>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// User Management Component
const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingUser, setEditingUser] = useState<any>(null);
  const [formData, setFormData] = useState({
    email: '',
    first_name: '',
    last_name: '',
    password: '',
    role: 'employee',
    is_active: true
  });

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      const data = await apiService.getUsers();
      setUsers(data);
    } catch (error) {
      toast.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingUser) {
        // Update user
        await apiService.updateUser(editingUser.id, formData);
        toast.success('User updated successfully!');
      } else {
        // Create user
        await apiService.createUser(formData);
        toast.success('User created successfully!');
      }
      setShowCreateModal(false);
      setEditingUser(null);
      setFormData({ email: '', first_name: '', last_name: '', password: '', role: 'employee', is_active: true });
      loadUsers();
    } catch (error) {
      console.error('Error saving user:', error);
    }
  };

  const handleDelete = async (id: string) => {
    if (confirm('Are you sure you want to deactivate this user? They will no longer be able to access the system.')) {
      try {
        await apiService.deleteUser(id);
        loadUsers();
      } catch (error) {
        console.error('Error deactivating user:', error);
      }
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900">User Management</h3>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn-primary"
        >
          Add User
        </button>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="max-h-96 overflow-y-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Role
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Login
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {users.map((user) => (
                <tr key={user.id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                        <span className="text-sm font-medium text-gray-700">
                          {user.first_name?.[0]}{user.last_name?.[0]}
                        </span>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">
                          {user.full_name || `${user.first_name} ${user.last_name}`}
                        </div>
                        <div className="text-sm text-gray-500">{user.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <span className={`inline-flex px-2 py-1 text-xs rounded-full ${
                      user.role === 'admin' 
                        ? 'bg-purple-100 text-purple-800' 
                        : 'bg-blue-100 text-blue-800'
                    }`}>
                      {user.role}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <span className={`inline-flex px-2 py-1 text-xs rounded-full ${
                      user.is_active 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {user.last_login || 'Never'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                    <button
                      onClick={() => {
                        setEditingUser(user);
                        setFormData({
                          email: user.email,
                          first_name: user.first_name || '',
                          last_name: user.last_name || '',
                          password: '', // Don't pre-fill password
                          role: user.role,
                          is_active: user.is_active
                        });
                        setShowCreateModal(true);
                      }}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(user.id)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Deactivate
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create/Edit Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 max-h-96 overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">
              {editingUser ? 'Edit User' : 'Create User'}
            </h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                  className="input-field"
                  required
                  disabled={!!editingUser} // Don't allow email changes for existing users
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  First Name
                </label>
                <input
                  type="text"
                  value={formData.first_name}
                  onChange={(e) => setFormData(prev => ({ ...prev, first_name: e.target.value }))}
                  className="input-field"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Last Name
                </label>
                <input
                  type="text"
                  value={formData.last_name}
                  onChange={(e) => setFormData(prev => ({ ...prev, last_name: e.target.value }))}
                  className="input-field"
                  required
                />
              </div>
              {!editingUser && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Password
                  </label>
                  <input
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                    className="input-field"
                    required={!editingUser}
                    placeholder={editingUser ? "Leave blank to keep current password" : ""}
                  />
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Role
                </label>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData(prev => ({ ...prev, role: e.target.value }))}
                  className="input-field"
                  required
                >
                  <option value="employee">Employee</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">Active User</span>
                </label>
              </div>
              <div className="flex space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setEditingUser(null);
                    setFormData({ email: '', first_name: '', last_name: '', password: '', role: 'employee', is_active: true });
                  }}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary flex-1">
                  {editingUser ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

// System Settings Component
const SystemSettings: React.FC<{ onSettingsUpdate?: () => void }> = ({ onSettingsUpdate }) => {
  const [settings, setSettings] = useState({
    site_name: 'Department Portal',
    max_file_size: '50',
    allowed_file_types: 'pdf,doc,docx,xls,xlsx,ppt,pptx,txt,jpg,png',
    enable_ai_chat: true,
    enable_document_sharing: true,
    require_document_approval: false,
    auto_backup_enabled: true,
    backup_frequency: 'daily',
    backup_retention_days: '30',
    password_expiry_days: '90',
    max_login_attempts: '5'
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [backups, setBackups] = useState<any[]>([]);
  const [loadingBackups, setLoadingBackups] = useState(false);
  const [creatingBackup, setCreatingBackup] = useState(false);

  useEffect(() => {
    loadSettings();
    loadBackups();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await apiService.getSystemSettings();
      setSettings({
        site_name: data.site_name || 'Department Portal',
        max_file_size: String(data.max_file_size || '50'),
        allowed_file_types: data.allowed_file_types || 'pdf,doc,docx,xls,xlsx,ppt,pptx,txt,jpg,png',
        enable_ai_chat: data.enable_ai_chat !== undefined ? data.enable_ai_chat : true,
        enable_document_sharing: data.enable_document_sharing !== undefined ? data.enable_document_sharing : true,
        require_document_approval: data.require_document_approval !== undefined ? data.require_document_approval : false,
        auto_backup_enabled: data.auto_backup_enabled !== undefined ? data.auto_backup_enabled : true,
        backup_frequency: data.backup_frequency || 'daily',
        backup_retention_days: String(data.backup_retention_days || '30'),
        password_expiry_days: String(data.password_expiry_days || '90'),
        max_login_attempts: String(data.max_login_attempts || '5')
      });
    } catch (error) {
      console.error('Failed to load settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadBackups = async () => {
    setLoadingBackups(true);
    try {
      const data = await apiService.getSystemBackups();
      setBackups(data);
    } catch (error) {
      console.error('Failed to load backups:', error);
    } finally {
      setLoadingBackups(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await apiService.updateSystemSettings(settings);
      toast.success('Settings saved successfully!');
      // Call the callback to refresh AI chat status
      if (onSettingsUpdate) {
        onSettingsUpdate();
      }
    } catch (error) {
      console.error('Failed to save settings:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleCreateBackup = async () => {
    setCreatingBackup(true);
    try {
      await apiService.createSystemBackup({
        name: `manual_backup_${new Date().toISOString().split('T')[0]}`,
        include_documents: true,
        include_database: true,
        include_settings: true,
        include_user_data: true
      });
      
      // Reload backups after creation
      setTimeout(() => {
        loadBackups();
      }, 2000);
    } catch (error) {
      console.error('Failed to create backup:', error);
    } finally {
      setCreatingBackup(false);
    }
  };

  const handleDownloadBackup = async (backupId: string) => {
    try {
      await apiService.downloadSystemBackup(backupId);
    } catch (error) {
      console.error('Failed to download backup:', error);
    }
  };

  const handleDeleteBackup = async (backupId: string, backupName: string) => {
    if (window.confirm(`Are you sure you want to delete backup "${backupName}"?`)) {
      try {
        await apiService.deleteSystemBackup(backupId);
        loadBackups();
      } catch (error) {
        console.error('Failed to delete backup:', error);
      }
    }
  };

  const formatFileSize = (sizeInMB: number) => {
    if (sizeInMB < 1) return `${(sizeInMB * 1024).toFixed(1)} KB`;
    return `${sizeInMB.toFixed(1)} MB`;
  };

  const formatDuration = (duration: string) => {
    if (!duration) return 'N/A';
    const match = duration.match(/(\d+):(\d+):(\d+)/);
    if (match) {
      const [, hours, minutes, seconds] = match;
      return `${hours}h ${minutes}m ${seconds}s`;
    }
    return duration;
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex-shrink-0 mb-6">
        <h3 className="text-lg font-semibold text-gray-900">System Settings</h3>
        <p className="text-sm text-gray-600 mt-1">Configure system-wide settings and manage backups</p>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-hidden">
        <div className="h-full overflow-y-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pb-6">
            
            {/* Settings Panel */}
            <div className="space-y-6">
              
              {/* General Settings */}
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h4 className="text-md font-medium text-gray-900 mb-4 flex items-center">
                  <span className="mr-2">⚙️</span>
                  General Settings
                </h4>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Site Name
                    </label>
                    <input
                      type="text"
                      value={settings.site_name}
                      onChange={(e) => setSettings({...settings, site_name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Max File Size (MB)
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="1000"
                      value={settings.max_file_size}
                      onChange={(e) => setSettings({...settings, max_file_size: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">Maximum file size for document uploads</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Allowed File Types
                    </label>
                    <input
                      type="text"
                      value={settings.allowed_file_types}
                      onChange={(e) => setSettings({...settings, allowed_file_types: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">Comma-separated list of allowed file extensions</p>
                  </div>
                </div>
              </div>

              {/* Feature Settings */}
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h4 className="text-md font-medium text-gray-900 mb-4 flex items-center">
                  <span className="mr-2">🎛️</span>
                  Feature Settings
                </h4>
                
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium text-gray-700">AI Chat Bot</label>
                      <p className="text-xs text-gray-500">Enable AI-powered document assistant</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.enable_ai_chat}
                        onChange={(e) => setSettings({...settings, enable_ai_chat: e.target.checked})}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium text-gray-700">Document Sharing</label>
                      <p className="text-xs text-gray-500">Allow users to share documents</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.enable_document_sharing}
                        onChange={(e) => setSettings({...settings, enable_document_sharing: e.target.checked})}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium text-gray-700">Document Approval</label>
                      <p className="text-xs text-gray-500">Require approval before documents are published</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.require_document_approval}
                        onChange={(e) => setSettings({...settings, require_document_approval: e.target.checked})}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                </div>
              </div>

              {/* Security Settings */}
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h4 className="text-md font-medium text-gray-900 mb-4 flex items-center">
                  <span className="mr-2">🔒</span>
                  Security Settings
                </h4>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Password Expiry (Days)
                    </label>
                    <input
                      type="number"
                      min="30"
                      max="365"
                      value={settings.password_expiry_days}
                      onChange={(e) => setSettings({...settings, password_expiry_days: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">Number of days before passwords expire</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Max Login Attempts
                    </label>
                    <input
                      type="number"
                      min="3"
                      max="10"
                      value={settings.max_login_attempts}
                      onChange={(e) => setSettings({...settings, max_login_attempts: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">Maximum login attempts before account lockout</p>
                  </div>
                </div>
              </div>

              {/* Backup Settings */}
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h4 className="text-md font-medium text-gray-900 mb-4 flex items-center">
                  <span className="mr-2">💾</span>
                  Backup Settings
                </h4>
                
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium text-gray-700">Auto Backup</label>
                      <p className="text-xs text-gray-500">Enable automatic system backups</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.auto_backup_enabled}
                        onChange={(e) => setSettings({...settings, auto_backup_enabled: e.target.checked})}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Backup Frequency
                    </label>
                    <select
                      value={settings.backup_frequency}
                      onChange={(e) => setSettings({...settings, backup_frequency: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="hourly">Hourly</option>
                      <option value="daily">Daily</option>
                      <option value="weekly">Weekly</option>
                      <option value="monthly">Monthly</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Backup Retention (Days)
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="365"
                      value={settings.backup_retention_days}
                      onChange={(e) => setSettings({...settings, backup_retention_days: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">Number of days to retain backups</p>
                  </div>
                </div>
              </div>

              {/* Save Button */}
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  {saving ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                      Saving...
                    </>
                  ) : (
                    <>
                      <span className="mr-2">💾</span>
                      Save Settings
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Backup Management Panel */}
            <div className="space-y-6">
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-md font-medium text-gray-900 flex items-center">
                    <span className="mr-2">📦</span>
                    Backup Management
                  </h4>
                  <button
                    onClick={handleCreateBackup}
                    disabled={creatingBackup}
                    className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm flex items-center"
                  >
                    {creatingBackup ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                        Creating...
                      </>
                    ) : (
                      <>
                        <span className="mr-2">💾</span>
                        Create Backup
                      </>
                    )}
                  </button>
                </div>

                {loadingBackups ? (
                  <div className="flex items-center justify-center py-8">
                    <LoadingSpinner />
                  </div>
                ) : (
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {backups.length === 0 ? (
                      <div className="text-center py-8 text-gray-500">
                        <span className="text-3xl mb-2 block">📦</span>
                        <p>No backups available</p>
                        <p className="text-xs">Create your first backup to get started</p>
                      </div>
                    ) : (
                      backups.map((backup) => (
                        <div
                          key={backup.id}
                          className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
                        >
                          <div className="flex items-center justify-between mb-2">
                            <h5 className="font-medium text-gray-900 truncate">{backup.name}</h5>
                            <div className="flex items-center space-x-2">
                              {backup.status === 'completed' && (
                                <>
                                  <button
                                    onClick={() => handleDownloadBackup(backup.id)}
                                    className="text-blue-600 hover:text-blue-800 text-sm"
                                    title="Download Backup"
                                  >
                                    ⬇️
                                  </button>
                                  <button
                                    onClick={() => handleDeleteBackup(backup.id, backup.name)}
                                    className="text-red-600 hover:text-red-800 text-sm"
                                    title="Delete Backup"
                                  >
                                    🗑️
                                  </button>
                                </>
                              )}
                            </div>
                          </div>
                          
                          <div className="grid grid-cols-2 gap-4 text-xs text-gray-600">
                            <div>
                              <span className="font-medium">Status:</span>
                              <span className={`ml-1 px-2 py-1 rounded-full text-xs ${
                                backup.status === 'completed' ? 'bg-green-100 text-green-800' :
                                backup.status === 'failed' ? 'bg-red-100 text-red-800' :
                                backup.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800' :
                                'bg-gray-100 text-gray-800'
                              }`}>
                                {backup.status}
                              </span>
                            </div>
                            <div>
                              <span className="font-medium">Size:</span>
                              <span className="ml-1">{formatFileSize(backup.file_size_mb || 0)}</span>
                            </div>
                            <div>
                              <span className="font-medium">Created:</span>
                              <span className="ml-1">{new Date(backup.created_at).toLocaleDateString()}</span>
                            </div>
                            <div>
                              <span className="font-medium">Duration:</span>
                              <span className="ml-1">{formatDuration(backup.duration)}</span>
                            </div>
                          </div>
                          
                          {backup.includes && (
                            <div className="mt-2 flex flex-wrap gap-1">
                              {backup.includes.documents && <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">Docs</span>}
                              {backup.includes.database && <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded">DB</span>}
                              {backup.includes.settings && <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">Settings</span>}
                              {backup.includes.user_data && <span className="px-2 py-1 bg-orange-100 text-orange-800 text-xs rounded">Users</span>}
                            </div>
                          )}
                          
                          {backup.error_message && (
                            <div className="mt-2 text-xs text-red-600 bg-red-50 p-2 rounded">
                              Error: {backup.error_message}
                            </div>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Permissions Management Component
const PermissionsManagement: React.FC = () => {
  const [activePermissionTab, setActivePermissionTab] = useState('users');
  const [users, setUsers] = useState<any[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [permissions, setPermissions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showPermissionModal, setShowPermissionModal] = useState(false);
  const [selectedEntity, setSelectedEntity] = useState<any>(null);
  const [entityType, setEntityType] = useState<'user' | 'department' | 'category'>('user');

  // Available permissions configuration
  const availablePermissions = {
    documents: [
      { key: 'documents.view_all', name: 'View All Documents', description: 'Can view all documents regardless of category' },
      { key: 'documents.create', name: 'Create Documents', description: 'Can upload and create new documents' },
      { key: 'documents.edit_all', name: 'Edit All Documents', description: 'Can edit any document in the system' },
      { key: 'documents.delete_all', name: 'Delete All Documents', description: 'Can delete any document in the system' },
      { key: 'documents.approve', name: 'Approve Documents', description: 'Can approve documents for publication' },
      { key: 'documents.share', name: 'Share Documents', description: 'Can share documents with users and departments' },
    ],
    categories: [
      { key: 'categories.view_all', name: 'View All Categories', description: 'Can view all document categories' },
      { key: 'categories.create', name: 'Create Categories', description: 'Can create new document categories' },
      { key: 'categories.edit', name: 'Edit Categories', description: 'Can modify existing categories' },
      { key: 'categories.delete', name: 'Delete Categories', description: 'Can delete categories' },
      { key: 'categories.assign', name: 'Assign Categories', description: 'Can assign categories to documents' },
    ],
    departments: [
      { key: 'departments.view_all', name: 'View All Departments', description: 'Can view all department information' },
      { key: 'departments.manage', name: 'Manage Departments', description: 'Can create, edit, and delete departments' },
      { key: 'departments.assign_users', name: 'Assign Users', description: 'Can assign users to departments' },
      { key: 'departments.view_employees', name: 'View Department Employees', description: 'Can see employee lists in departments' },
    ],
    users: [
      { key: 'users.view_all', name: 'View All Users', description: 'Can view all user profiles and information' },
      { key: 'users.create', name: 'Create Users', description: 'Can create new user accounts' },
      { key: 'users.edit', name: 'Edit Users', description: 'Can modify user accounts and profiles' },
      { key: 'users.deactivate', name: 'Deactivate Users', description: 'Can deactivate user accounts' },
      { key: 'users.assign_roles', name: 'Assign Roles', description: 'Can change user roles and permissions' },
    ],
    system: [
      { key: 'system.admin_settings', name: 'Admin Settings', description: 'Can access admin settings panel' },
      { key: 'system.view_analytics', name: 'View Analytics', description: 'Can view system analytics and reports' },
      { key: 'system.manage_settings', name: 'Manage Settings', description: 'Can modify system configuration' },
      { key: 'system.backup', name: 'Backup Management', description: 'Can manage system backups' },
    ]
  };

  useEffect(() => {
    loadPermissionData();
  }, []);

  const loadPermissionData = async () => {
    setLoading(true);
    try {
      const [usersData, departmentsData, categoriesData, permissionsData] = await Promise.all([
        apiService.getUsers(),
        apiService.getDepartments(),
        apiService.getCategories(),
        apiService.getAllPermissions()
      ]);
      
      setUsers(usersData);
      setDepartments(departmentsData);
      setCategories(categoriesData);
      setPermissions(permissionsData);
    } catch (error) {
      toast.error('Failed to load permission data');
      console.error('Permission data load error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGrantPermission = async (entity: any, permissionKey: string) => {
    try {
      await apiService.grantPermission({
        entityType: entityType,
        entityId: entity.id,
        permission: permissionKey
      });
      
      // Reload permissions to get updated data
      const updatedPermissions = await apiService.getAllPermissions();
      setPermissions(updatedPermissions);
    } catch (error) {
      console.error('Failed to grant permission:', error);
    }
  };

  const handleRevokePermission = async (permissionId: string) => {
    try {
      await apiService.revokePermission(permissionId);
      
      // Reload permissions to get updated data
      const updatedPermissions = await apiService.getAllPermissions();
      setPermissions(updatedPermissions);
    } catch (error) {
      console.error('Failed to revoke permission:', error);
    }
  };

  const getEntityPermissions = (entity: any) => {
    return permissions.filter(p => 
      p.entity_type === entityType && 
      p.entity_id === entity.id
    );
  };

  const hasPermission = (entity: any, permissionKey: string) => {
    return getEntityPermissions(entity).some(p => p.permission === permissionKey);
  };

  const permissionTabs = [
    { id: 'users', name: 'User Permissions', icon: '👤', description: 'Manage individual user permissions' },
    { id: 'departments', name: 'Department Permissions', icon: '🏢', description: 'Manage department-level permissions' }
  ];

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Permissions Management</h3>
          <p className="text-sm text-gray-600 mt-1">Control access and permissions for users and departments</p>
        </div>
        <div className="flex space-x-2">
          <button 
            onClick={async () => {
              try {
                const report = await apiService.getPermissionReport();
                console.log('Permission Report:', report);
                toast.success('Permission report generated - check console for details');
              } catch (error) {
                console.error('Failed to generate report:', error);
              }
            }}
            className="btn-secondary"
          >
            📊 Permission Report
          </button>
        </div>
      </div>

      {/* Permission Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8 overflow-x-auto">
          {permissionTabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => {
                setActivePermissionTab(tab.id);
                setEntityType(tab.id as any);
              }}
              className={`py-3 px-1 border-b-2 font-medium text-sm whitespace-nowrap transition-colors ${
                activePermissionTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center space-x-2">
                <span>{tab.icon}</span>
                <span>{tab.name}</span>
              </div>
              <p className="text-xs text-gray-400 mt-1">{tab.description}</p>
            </button>
          ))}
        </nav>
      </div>

      {/* User Permissions */}
      {activePermissionTab === 'users' && (
        <div className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <span className="text-blue-600">ℹ️</span>
              <div>
                <h4 className="text-sm font-medium text-blue-900">User Permission Management</h4>
                <p className="text-sm text-blue-700">Grant specific permissions to individual users beyond their basic role.</p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {users.map((user) => (
              <div key={user.id} className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
                      <span className="text-sm font-medium text-gray-600">
                        {user.first_name?.[0]}{user.last_name?.[0]}
                      </span>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">
                        {user.full_name || `${user.first_name} ${user.last_name}`}
                      </h4>
                      <p className="text-xs text-gray-500">{user.email}</p>
                      <span className={`inline-flex px-2 py-1 text-xs rounded-full mt-1 ${
                        user.role === 'admin' 
                          ? 'bg-purple-100 text-purple-700' 
                          : 'bg-blue-100 text-blue-700'
                      }`}>
                        {user.role}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      setSelectedEntity(user);
                      setEntityType('user');
                      setShowPermissionModal(true);
                    }}
                    className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                  >
                    Manage Permissions
                  </button>
                </div>
                
                <div className="space-y-2">
                  <h5 className="text-xs font-medium text-gray-700 uppercase tracking-wider">Active Permissions</h5>
                  {getEntityPermissions(user).length === 0 ? (
                    <p className="text-xs text-gray-500">No additional permissions granted</p>
                  ) : (
                    <div className="space-y-1">
                      {getEntityPermissions(user).slice(0, 3).map((permission) => (
                        <div key={permission.id} className="flex items-center justify-between text-xs">
                          <span className="text-gray-600">{permission.permission}</span>
                          <button
                            onClick={() => handleRevokePermission(permission.id)}
                            className="text-red-500 hover:text-red-700"
                          >
                            Revoke
                          </button>
                        </div>
                      ))}
                      {getEntityPermissions(user).length > 3 && (
                        <p className="text-xs text-gray-400">+{getEntityPermissions(user).length - 3} more...</p>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Department Permissions */}
      {activePermissionTab === 'departments' && (
        <div className="space-y-4">
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <span className="text-green-600">🏢</span>
              <div>
                <h4 className="text-sm font-medium text-green-900">Department Permission Management</h4>
                <p className="text-sm text-green-700">Control what each department can access and manage.</p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {departments.map((dept) => (
              <div key={dept.id} className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">{dept.name}</h4>
                    <p className="text-xs text-gray-500">Code: {dept.code}</p>
                    <p className="text-xs text-gray-400">{dept.employees_count || 0} employees</p>
                  </div>
                  <button
                    onClick={() => {
                      setSelectedEntity(dept);
                      setEntityType('department');
                      setShowPermissionModal(true);
                    }}
                    className="text-green-600 hover:text-green-800 text-sm font-medium"
                  >
                    Manage Access
                  </button>
                </div>
                
                <div className="space-y-2">
                  <h5 className="text-xs font-medium text-gray-700 uppercase tracking-wider">Department Access</h5>
                  {getEntityPermissions(dept).length === 0 ? (
                    <p className="text-xs text-gray-500">Default access permissions</p>
                  ) : (
                    <div className="space-y-1">
                      {getEntityPermissions(dept).slice(0, 3).map((permission) => (
                        <div key={permission.id} className="flex items-center justify-between text-xs">
                          <span className="text-gray-600">{permission.permission}</span>
                          <button
                            onClick={() => handleRevokePermission(permission.id)}
                            className="text-red-500 hover:text-red-700"
                          >
                            Remove
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Permission Assignment Modal */}
      {showPermissionModal && selectedEntity && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Manage Permissions for {selectedEntity.name || selectedEntity.email || selectedEntity.title}
                </h3>
                <p className="text-sm text-gray-600">
                  Grant or revoke specific permissions for this {entityType}
                </p>
              </div>
              <button
                onClick={() => setShowPermissionModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div className="space-y-6">
              {Object.entries(availablePermissions).map(([category, perms]) => (
                <div key={category} className="border border-gray-200 rounded-lg p-4">
                  <h4 className="text-md font-medium text-gray-900 mb-4 capitalize">
                    {category} Permissions
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {perms.map((permission) => (
                      <div key={permission.key} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3">
                            <input
                              type="checkbox"
                              checked={hasPermission(selectedEntity, permission.key)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  handleGrantPermission(selectedEntity, permission.key);
                                } else {
                                  const existingPermission = getEntityPermissions(selectedEntity)
                                    .find(p => p.permission === permission.key);
                                  if (existingPermission) {
                                    handleRevokePermission(existingPermission.id);
                                  }
                                }
                              }}
                              className="w-4 h-4 text-blue-600 rounded"
                            />
                            <div>
                              <h5 className="text-sm font-medium text-gray-900">{permission.name}</h5>
                              <p className="text-xs text-gray-500">{permission.description}</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-end space-x-3 mt-6 pt-4 border-t">
              <button
                onClick={() => setShowPermissionModal(false)}
                className="btn-secondary"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Main Admin Settings Component
const AdminSettings: React.FC = () => {
  const [activeTab, setActiveTab] = useState('categories');
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAdminStatus();
  }, []);

  const checkAdminStatus = async () => {
    try {
      const adminStatus = await apiService.isAdmin();
      setIsAdmin(adminStatus);
    } catch (error) {
      setIsAdmin(false);
    } finally {
      setLoading(false);
    }
  };

  // Callback to refresh AI chat status when settings change
  const handleSettingsUpdate = () => {
    // Trigger a page reload to refresh AI chat status
    setTimeout(() => {
      window.location.reload();
    }, 1500);
  };

  const tabs = [
    { id: 'categories', name: 'Categories', icon: '📁' },
    { id: 'departments', name: 'Departments', icon: '🏢' },
    { id: 'users', name: 'Users', icon: '👥' },
    { id: 'permissions', name: 'Permissions', icon: '🔐' },
    { id: 'settings', name: 'System Settings', icon: '⚙️' }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="text-red-500 text-6xl mb-4">🚫</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Access Denied</h2>
          <p className="text-gray-600">You don't have permission to access admin settings.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <div className="flex-shrink-0 mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Admin Settings</h1>
        <p className="text-gray-600 mt-1">Manage your portal's configuration and data</p>
      </div>

      {/* Tabs */}
      <div className="flex-shrink-0 border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content with proper scrolling */}
      <div className="flex-1 min-h-0">
        {activeTab === 'categories' && <CategoryManagement />}
        {activeTab === 'departments' && <DepartmentManagement />}
        {activeTab === 'users' && <UserManagement />}
        {activeTab === 'permissions' && <PermissionsManagement />}
        {activeTab === 'settings' && <SystemSettings onSettingsUpdate={handleSettingsUpdate} />}
      </div>
    </div>
  );
};

export default AdminSettings; 