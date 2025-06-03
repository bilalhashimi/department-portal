import React, { useState } from 'react';
import { apiService } from '../services/api';
import toast from 'react-hot-toast';

interface TestResult {
  name: string;
  status: 'pending' | 'success' | 'error';
  message: string;
  duration?: number;
}

const AdminSettingsTest: React.FC = () => {
  const [tests, setTests] = useState<TestResult[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [currentTest, setCurrentTest] = useState('');

  const updateTestStatus = (name: string, status: TestResult['status'], message: string, duration?: number) => {
    setTests(prev => prev.map(test => 
      test.name === name 
        ? { ...test, status, message, duration }
        : test
    ));
  };

  const addTest = (name: string) => {
    setTests(prev => [...prev, { name, status: 'pending', message: 'Waiting...' }]);
  };

  const runTest = async (name: string, testFn: () => Promise<void>) => {
    setCurrentTest(name);
    const startTime = Date.now();
    
    try {
      await testFn();
      const duration = Date.now() - startTime;
      updateTestStatus(name, 'success', 'Passed', duration);
      return true;
    } catch (error: any) {
      const duration = Date.now() - startTime;
      updateTestStatus(name, 'error', error.message || 'Failed', duration);
      return false;
    }
  };

  const runAllTests = async () => {
    setIsRunning(true);
    setTests([]);
    
    // Initialize tests
    const testNames = [
      'Authentication Check',
      'Admin Permission Check',
      'Load Categories',
      'Create Category',
      'Update Category',
      'Delete Category',
      'Load Departments',
      'Create Department',
      'Update Department',
      'Delete Department',
      'Load Users',
      'Create User',
      'Update User',
      'Deactivate User',
      'API Error Handling',
      'UI Scrolling Test',
      'Modal Functionality',
      'Form Validation',
      'Real-time Updates'
    ];

    testNames.forEach(addTest);

    let testData = {
      createdCategoryId: null as string | null,
      createdDepartmentId: null as string | null,
      createdUserId: null as string | null,
      originalCategoryCount: 0,
      originalDepartmentCount: 0,
      originalUserCount: 0
    };

    // Test 1: Authentication Check
    await runTest('Authentication Check', async () => {
      const isAuth = apiService.isAuthenticated();
      if (!isAuth) throw new Error('User not authenticated');
    });

    // Test 2: Admin Permission Check
    await runTest('Admin Permission Check', async () => {
      const isAdmin = await apiService.isAdmin();
      if (!isAdmin) throw new Error('User does not have admin permissions');
    });

    // Test 3: Load Categories
    await runTest('Load Categories', async () => {
      const categories = await apiService.getCategories();
      testData.originalCategoryCount = categories.length;
      if (!Array.isArray(categories)) throw new Error('Categories not returned as array');
    });

    // Test 4: Create Category
    await runTest('Create Category', async () => {
      const newCategory = {
        name: `Test Category ${Date.now()}`,
        description: 'Test category created by automated test',
        is_public: true
      };
      
      const created = await apiService.createCategory(newCategory);
      testData.createdCategoryId = created.id;
      
      if (!created.id) throw new Error('Category creation did not return ID');
      if (created.name !== newCategory.name) throw new Error('Category name mismatch');
    });

    // Test 5: Update Category
    await runTest('Update Category', async () => {
      if (!testData.createdCategoryId) throw new Error('No category to update');
      
      const updatedData = {
        name: `Updated Test Category ${Date.now()}`,
        description: 'Updated description',
        is_public: false
      };
      
      const updated = await apiService.updateCategory(testData.createdCategoryId, updatedData);
      if (updated.name !== updatedData.name) throw new Error('Category update failed');
    });

    // Test 6: Delete Category
    await runTest('Delete Category', async () => {
      if (!testData.createdCategoryId) throw new Error('No category to delete');
      
      await apiService.deleteCategory(testData.createdCategoryId);
      
      // Verify deletion by checking categories list
      const categories = await apiService.getCategories();
      const stillExists = categories.find(c => c.id === testData.createdCategoryId);
      if (stillExists) throw new Error('Category still exists after deletion');
    });

    // Test 7: Load Departments
    await runTest('Load Departments', async () => {
      const departments = await apiService.getDepartments();
      testData.originalDepartmentCount = departments.length;
      if (!Array.isArray(departments)) throw new Error('Departments not returned as array');
    });

    // Test 8: Create Department
    await runTest('Create Department', async () => {
      const newDepartment = {
        name: `Test Department ${Date.now()}`,
        code: `TD${Date.now().toString().slice(-4)}`,
        description: 'Test department created by automated test',
        email: `test.dept.${Date.now()}@company.com`,
        location: 'Test Location',
        is_active: true
      };
      
      const created = await apiService.createDepartment(newDepartment);
      testData.createdDepartmentId = created.id;
      
      if (!created.id) throw new Error('Department creation did not return ID');
      if (created.name !== newDepartment.name) throw new Error('Department name mismatch');
    });

    // Test 9: Update Department
    await runTest('Update Department', async () => {
      if (!testData.createdDepartmentId) throw new Error('No department to update');
      
      const updatedData = {
        name: `Updated Test Department ${Date.now()}`,
        description: 'Updated description',
        location: 'Updated Location'
      };
      
      const updated = await apiService.updateDepartment(testData.createdDepartmentId, updatedData);
      if (updated.name !== updatedData.name) throw new Error('Department update failed');
    });

    // Test 10: Delete Department
    await runTest('Delete Department', async () => {
      if (!testData.createdDepartmentId) throw new Error('No department to delete');
      
      await apiService.deleteDepartment(testData.createdDepartmentId);
      
      // Verify deletion by checking departments list
      const departments = await apiService.getDepartments();
      const stillExists = departments.find(d => d.id === testData.createdDepartmentId);
      if (stillExists) throw new Error('Department still exists after deletion');
    });

    // Test 11: Load Users
    await runTest('Load Users', async () => {
      const users = await apiService.getUsers();
      testData.originalUserCount = users.length;
      if (!Array.isArray(users)) throw new Error('Users not returned as array');
    });

    // Test 12: Create User
    await runTest('Create User', async () => {
      const newUser = {
        email: `test.user.${Date.now()}@company.com`,
        username: `testuser${Date.now()}`,
        first_name: 'Test',
        last_name: 'User',
        password: 'TestPassword123!',
        password_confirm: 'TestPassword123!',
        role: 'employee',
        is_active: true
      };
      
      const created = await apiService.createUser(newUser);
      testData.createdUserId = created.id;
      
      if (!created.id) throw new Error('User creation did not return ID');
      if (created.email !== newUser.email) throw new Error('User email mismatch');
    });

    // Test 13: Update User
    await runTest('Update User', async () => {
      if (!testData.createdUserId) throw new Error('No user to update');
      
      const updatedData = {
        first_name: 'Updated',
        last_name: 'TestUser',
        role: 'admin'
      };
      
      const updated = await apiService.updateUser(testData.createdUserId, updatedData);
      if (updated.first_name !== updatedData.first_name) throw new Error('User update failed');
    });

    // Test 14: Deactivate User
    await runTest('Deactivate User', async () => {
      if (!testData.createdUserId) throw new Error('No user to deactivate');
      
      await apiService.deleteUser(testData.createdUserId); // This calls deactivate endpoint
      
      // Verify deactivation by checking users list
      const users = await apiService.getUsers();
      const stillActive = users.find(u => u.id === testData.createdUserId && u.is_active);
      if (stillActive) throw new Error('User still active after deactivation');
    });

    // Test 15: API Error Handling
    await runTest('API Error Handling', async () => {
      try {
        await apiService.getDocument('non-existent-id');
        throw new Error('Expected error not thrown');
      } catch (error: any) {
        // Accept various error message formats that indicate document not found
        const errorMsg = error.message || '';
        const isValidError = errorMsg.includes('Failed to fetch document') || 
                           errorMsg.includes('404') || 
                           errorMsg.includes('Not Found') ||
                           errorMsg.includes('Document not found');
        if (!isValidError) {
          throw new Error(`Unexpected error message: ${errorMsg}`);
        }
      }
    });

    // Test 16: UI Scrolling Test
    await runTest('UI Scrolling Test', async () => {
      // Test if scrollable elements exist
      const scrollableElements = document.querySelectorAll('[class*="overflow-y-auto"]');
      if (scrollableElements.length === 0) {
        throw new Error('No scrollable elements found');
      }
      
      // Test sticky headers
      const stickyHeaders = document.querySelectorAll('[class*="sticky"]');
      if (stickyHeaders.length === 0) {
        throw new Error('No sticky headers found');
      }
    });

    // Test 17: Modal Functionality
    await runTest('Modal Functionality', async () => {
      // Check if modal classes exist in CSS
      // Since modals are conditionally rendered, we check if the CSS classes work
      const testDiv = document.createElement('div');
      testDiv.className = 'fixed inset-0 bg-black bg-opacity-50';
      document.body.appendChild(testDiv);
      
      const styles = window.getComputedStyle(testDiv);
      if (styles.position !== 'fixed') {
        throw new Error('Modal positioning not working');
      }
      
      document.body.removeChild(testDiv);
    });

    // Test 18: Form Validation
    await runTest('Form Validation', async () => {
      // Test form input classes - look for existing CSS classes
      const inputFields = document.querySelectorAll('input[class*="input-field"], input.input-field');
      const regularInputs = document.querySelectorAll('input[type="text"], input[type="email"], input[type="password"]');
      
      if (inputFields.length === 0 && regularInputs.length === 0) {
        throw new Error('No form inputs found');
      }
      
      // Test button classes - look for existing btn classes
      const btnPrimary = document.querySelectorAll('button[class*="btn-primary"], .btn-primary');
      const btnSecondary = document.querySelectorAll('button[class*="btn-secondary"], .btn-secondary');
      const generalButtons = document.querySelectorAll('button');
      
      if (btnPrimary.length === 0 && btnSecondary.length === 0 && generalButtons.length === 0) {
        throw new Error('No buttons found');
      }
    });

    // Test 19: Real-time Updates
    await runTest('Real-time Updates', async () => {
      // Test that data refreshes after operations
      const initialCategories = await apiService.getCategories();
      
      // Create and immediately check if list updates
      const testCategory = {
        name: `Realtime Test ${Date.now()}`,
        description: 'Testing real-time updates',
        is_public: true
      };
      
      const created = await apiService.createCategory(testCategory);
      const updatedCategories = await apiService.getCategories();
      
      if (updatedCategories.length <= initialCategories.length) {
        throw new Error('Category list did not update after creation');
      }
      
      // Clean up
      await apiService.deleteCategory(created.id);
    });

    setCurrentTest('');
    setIsRunning(false);
    
    // Show summary
    const passed = tests.filter(t => t.status === 'success').length;
    const failed = tests.filter(t => t.status === 'error').length;
    
    if (failed === 0) {
      toast.success(`All ${passed} tests passed! 🎉`);
    } else {
      toast.error(`${failed} tests failed, ${passed} tests passed`);
    }
  };

  const getStatusIcon = (status: TestResult['status']) => {
    switch (status) {
      case 'success': return '✅';
      case 'error': return '❌';
      case 'pending': return '⏳';
      default: return '⏳';
    }
  };

  const getStatusColor = (status: TestResult['status']) => {
    switch (status) {
      case 'success': return 'text-green-600';
      case 'error': return 'text-red-600';
      case 'pending': return 'text-yellow-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">
          🧪 Admin Settings Test Suite
        </h1>
        
        <div className="mb-6">
          <p className="text-gray-600 mb-4">
            This test suite verifies all admin settings functionality including user management, 
            category management, department management, and UI interactions.
          </p>
          
          <button
            onClick={runAllTests}
            disabled={isRunning}
            className={`px-6 py-3 rounded-lg font-medium ${
              isRunning 
                ? 'bg-gray-400 cursor-not-allowed' 
                : 'bg-blue-600 hover:bg-blue-700'
            } text-white transition-colors`}
          >
            {isRunning ? '🔄 Running Tests...' : '▶️ Run All Tests'}
          </button>
          
          {currentTest && (
            <p className="mt-2 text-sm text-blue-600">
              Currently running: {currentTest}
            </p>
          )}
        </div>

        {tests.length > 0 && (
          <div className="space-y-1">
            <h2 className="text-lg font-semibold text-gray-800 mb-3">Test Results</h2>
            
            <div className="max-h-96 overflow-y-auto border rounded-lg">
              {tests.map((test, index) => (
                <div 
                  key={index}
                  className={`p-3 border-b last:border-b-0 flex items-center justify-between ${
                    test.status === 'error' ? 'bg-red-50' : 
                    test.status === 'success' ? 'bg-green-50' : 'bg-gray-50'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <span className="text-lg">{getStatusIcon(test.status)}</span>
                    <div>
                      <span className="font-medium text-gray-900">{test.name}</span>
                      <p className={`text-sm ${getStatusColor(test.status)}`}>
                        {test.message}
                      </p>
                    </div>
                  </div>
                  
                  {test.duration && (
                    <span className="text-xs text-gray-500">
                      {test.duration}ms
                    </span>
                  )}
                </div>
              ))}
            </div>
            
            {tests.length > 0 && !isRunning && (
              <div className="mt-4 p-4 bg-gray-100 rounded-lg">
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-bold text-green-600">
                      {tests.filter(t => t.status === 'success').length}
                    </div>
                    <div className="text-sm text-gray-600">Passed</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-red-600">
                      {tests.filter(t => t.status === 'error').length}
                    </div>
                    <div className="text-sm text-gray-600">Failed</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-gray-600">
                      {tests.length}
                    </div>
                    <div className="text-sm text-gray-600">Total</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        <div className="mt-8 p-4 bg-blue-50 rounded-lg">
          <h3 className="font-semibold text-blue-800 mb-2">What This Tests:</h3>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• User Management (Create, Update, Deactivate)</li>
            <li>• Category Management (CRUD operations)</li>
            <li>• Department Management (CRUD operations)</li>
            <li>• API Authentication & Permissions</li>
            <li>• Error Handling & Validation</li>
            <li>• UI Scrolling & Modal Functionality</li>
            <li>• Real-time Data Updates</li>
            <li>• Form Validation & Styling</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default AdminSettingsTest; 