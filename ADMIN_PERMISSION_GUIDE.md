# Django Admin Permission Management Guide

## 🎯 **Overview**

The Department Portal now has **full integration** between the custom permission system and Django Admin. You can now see and manage the **actual permissions that control system functionality** directly in Django Admin.

## 🔍 **The Problem We Solved**

Previously, there were **TWO SEPARATE** permission systems:
- **Django's built-in permissions** (visible in admin but not used by the system)
- **Custom permissions** (used by the system but not visible in admin)

**Now they are unified!** ✅

## 🚀 **Quick Access Points**

| **What You Want to Do** | **Where to Go** |
|-------------------------|------------------|
| Manage user permissions | `/admin/accounts/user/` → Select user → Scroll to "Custom Permissions" |
| View all permissions | `/admin/departments/permission/` |
| Create permission templates | `/admin/departments/permissiontemplate/` |
| Audit permission changes | `/admin/departments/permissionauditlog/` |
| Manage departments | `/admin/departments/department/` |

## 👤 **Managing User Permissions**

### **Method 1: Direct User Admin (Recommended)**

1. Go to **`/admin/accounts/user/`**
2. Click on any user
3. Scroll down to **"Custom Permissions (Department Portal)"** section
4. Click **"Add another Custom Permission"**
5. Select from predefined permission choices
6. Click **Save**

### **Method 2: Permission Admin**

1. Go to **`/admin/departments/permission/`**
2. Click **"Add Permission"**
3. Fill in the form:
   - **Permission**: Choose from dropdown (e.g., "Documents: View All Documents")
   - **Entity Type**: Select "User"
   - **Entity ID**: Enter the user's UUID
   - **Expires At**: Optional expiration date
   - **Notes**: Why you're granting this permission

## 📋 **Available Permissions**

### **Document Permissions**
- `documents.view_all` - View All Documents
- `documents.create` - Create Documents
- `documents.edit_all` - Edit All Documents
- `documents.delete_all` - Delete All Documents
- `documents.approve` - Approve Documents
- `documents.share` - Share Documents
- `documents.download` - Download Documents
- `documents.view_stats` - View Statistics

### **Category Permissions**
- `categories.view_all` - View All Categories
- `categories.create` - Create Categories
- `categories.edit` - Edit Categories
- `categories.delete` - Delete Categories
- `categories.assign` - Assign to Documents

### **Department Permissions**
- `departments.view_all` - View All Departments
- `departments.manage` - Manage Departments
- `departments.assign_users` - Assign Users
- `departments.view_employees` - View Employee List
- `departments.manage_budget` - Manage Budget

### **User Permissions**
- `users.view_all` - View All Users
- `users.create` - Create Users
- `users.edit` - Edit Users
- `users.deactivate` - Deactivate Users
- `users.assign_roles` - Assign Roles
- `users.manage_permissions` - Manage Permissions

### **System Permissions**
- `system.admin_settings` - Access Admin Settings
- `system.view_analytics` - View Analytics
- `system.manage_settings` - Manage System Settings
- `system.backup` - Manage Backups
- `system.view_logs` - View System Logs
- `system.manage_templates` - Manage Permission Templates

## 📝 **Permission Templates**

Use templates to quickly assign common permission sets:

### **Available Templates:**
- **Document Manager**: Full document management
- **Document Viewer**: Basic viewing permissions
- **Department Head**: Department oversight permissions
- **HR Manager**: Human resources permissions
- **System Administrator**: Full system access

### **Using Templates:**
1. Go to **`/admin/departments/permissiontemplate/`**
2. Click on a template to view/edit
3. Use the template via the Admin Settings interface (frontend)

## 🔍 **Viewing Current Permissions**

### **For a Specific User:**
1. Go to **`/admin/accounts/user/`**
2. Look at the **"Custom Permissions"** column
3. Click on the user to see detailed permissions

### **All Permissions:**
1. Go to **`/admin/departments/permission/`**
2. Use filters to narrow down:
   - **Entity Type**: user, department, category
   - **Permission Category**: documents, categories, departments, users, system
   - **Is Active**: Yes/No
   - **Granted At**: Date range

## 📊 **Permission Audit Trail**

Track all permission changes at **`/admin/departments/permissionauditlog/`**

View:
- Who granted/revoked permissions
- When changes were made
- IP addresses and user agents
- Notes and context

## ⚠️ **Important Notes**

### **Entity ID Requirements:**
- **For users**: Use the user's UUID (found in user admin URL)
- **For departments**: Use the department's UUID
- **For categories**: Use the category's UUID

### **Permission Categories:**
- Automatically set based on permission choice
- No need to manually select

### **Permission Conflicts:**
- Custom permissions **override** Django built-in permissions
- System checks custom permissions first
- Admin role always has full access

## 🛠️ **Troubleshooting**

### **"User can still access despite no permissions"**
- Check if user has admin role (overrides all permissions)
- Verify permission is marked as "Active"
- Check permission audit log for recent changes

### **"Permission not working"**
- Ensure exact permission key is used
- Check entity_id matches exactly
- Verify permission hasn't expired

### **"Can't find user UUID"**
1. Go to user admin page
2. Click "Edit" on the user
3. UUID is in the URL: `/admin/accounts/user/{UUID}/change/`

## 🎯 **Best Practices**

### **1. Use Descriptive Notes**
Always add notes explaining why you granted permissions:
```
"Temporary document manager access for Q4 reporting project"
"Granted by John Smith for HR onboarding process"
```

### **2. Set Expiration Dates**
For temporary permissions, always set expiration:
- Contractor access: End of contract
- Project access: End of project
- Temporary elevation: Specific date

### **3. Regular Auditing**
- Review permissions monthly
- Check audit logs for unusual activity
- Remove inactive user permissions

### **4. Use Templates**
- Create templates for common roles
- Reduces manual errors
- Ensures consistency

## 🚀 **Quick Actions**

### **Grant Document Viewing to New Employee:**
1. Go to `/admin/accounts/user/{user-id}/change/`
2. Add permission: "Documents: View All Documents"
3. Add note: "New employee onboarding"
4. Save

### **Create Department Manager:**
1. Use "Department Head" template, or
2. Grant individual permissions:
   - `documents.view_all`
   - `documents.create`
   - `documents.approve`
   - `departments.view_employees`
   - `departments.manage_budget`

### **Temporary Admin Access:**
1. Grant `system.admin_settings`
2. Set expiration date
3. Add detailed notes
4. Monitor via audit log

## 📞 **Support**

If you need help:
1. Check this guide
2. Review audit logs for similar changes
3. Test permissions in a browser incognito window
4. Contact system administrator

---

**✅ You now have complete control over the permission system through Django Admin!** 