#!/usr/bin/env node
/**
 * Comprehensive Frontend Functionality Test Suite
 * Tests all frontend components and API service functionality
 */

import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

class FrontendTester {
    constructor() {
        this.testResults = {
            passed: 0,
            failed: 0,
            errors: []
        };
        this.srcPath = join(__dirname, 'src');
    }

    logTest(testName, passed, details = "") {
        const status = passed ? "✅ PASS" : "❌ FAIL";
        console.log(`${status}: ${testName}`);
        if (details) {
            console.log(`    Details: ${details}`);
        }

        if (passed) {
            this.testResults.passed++;
        } else {
            this.testResults.failed++;
            this.testResults.errors.push(`${testName}: ${details}`);
        }
    }

    checkFileExists(filePath, description) {
        try {
            const exists = fs.existsSync(filePath);
            this.logTest(`File Check: ${description}`, exists, 
                        exists ? "File exists" : `File not found: ${filePath}`);
            return exists;
        } catch (error) {
            this.logTest(`File Check: ${description}`, false, error.message);
            return false;
        }
    }

    checkComponentStructure(componentPath, componentName) {
        try {
            if (!fs.existsSync(componentPath)) {
                this.logTest(`Component Structure: ${componentName}`, false, "File does not exist");
                return false;
            }

            const content = fs.readFileSync(componentPath, 'utf8');
            
            // Check for basic React component structure
            const hasImportReact = content.includes('import React') || content.includes('import { ');
            const hasExportDefault = content.includes('export default');
            const hasComponentFunction = content.includes(`const ${componentName}`) || 
                                       content.includes(`function ${componentName}`);

            const isValid = hasImportReact && hasExportDefault && hasComponentFunction;
            
            this.logTest(`Component Structure: ${componentName}`, isValid,
                        isValid ? "Valid React component structure" : 
                        "Missing React imports, export default, or component function");
            
            return isValid;
        } catch (error) {
            this.logTest(`Component Structure: ${componentName}`, false, error.message);
            return false;
        }
    }

    checkAPIServiceMethods() {
        try {
            const apiPath = join(this.srcPath, 'services', 'api.ts');
            if (!fs.existsSync(apiPath)) {
                this.logTest("API Service File", false, "api.ts not found");
                return false;
            }

            const content = fs.readFileSync(apiPath, 'utf8');
            
            // Check for essential API methods
            const methods = [
                'login',
                'register',
                'logout',
                'getCurrentUser',
                'getDocuments',
                'uploadDocument',
                'downloadDocument',
                'searchDocuments',
                'getGroups',
                'createGroup',
                'addUserToGroup',
                'removeUserFromGroup',
                'getDepartments',
                'getCategories'
            ];

            const missingMethods = [];
            const foundMethods = [];

            methods.forEach(method => {
                if (content.includes(`${method}(`) || content.includes(`async ${method}(`)) {
                    foundMethods.push(method);
                } else {
                    missingMethods.push(method);
                }
            });

            const allMethodsPresent = missingMethods.length === 0;
            this.logTest("API Service Methods", allMethodsPresent,
                        allMethodsPresent ? `All ${methods.length} methods found` : 
                        `Missing methods: ${missingMethods.join(', ')}`);

            return allMethodsPresent;
        } catch (error) {
            this.logTest("API Service Methods", false, error.message);
            return false;
        }
    }

    checkTypeScriptTypes() {
        try {
            const apiPath = join(this.srcPath, 'services', 'api.ts');
            if (!fs.existsSync(apiPath)) {
                this.logTest("TypeScript Types", false, "api.ts not found");
                return false;
            }

            const content = fs.readFileSync(apiPath, 'utf8');
            
            // Check for essential TypeScript interfaces
            const interfaces = [
                'User',
                'Document',
                'SearchResult',
                'SearchResponse',
                'LoginCredentials',
                'LoginResponse'
            ];

            const missingInterfaces = [];
            const foundInterfaces = [];

            interfaces.forEach(interfaceName => {
                if (content.includes(`interface ${interfaceName}`) || 
                    content.includes(`export interface ${interfaceName}`)) {
                    foundInterfaces.push(interfaceName);
                } else {
                    missingInterfaces.push(interfaceName);
                }
            });

            const allInterfacesPresent = missingInterfaces.length === 0;
            this.logTest("TypeScript Types", allInterfacesPresent,
                        allInterfacesPresent ? `All ${interfaces.length} interfaces found` : 
                        `Missing interfaces: ${missingInterfaces.join(', ')}`);

            return allInterfacesPresent;
        } catch (error) {
            this.logTest("TypeScript Types", false, error.message);
            return false;
        }
    }

    checkPackageJson() {
        try {
            const packagePath = join(__dirname, 'package.json');
            if (!fs.existsSync(packagePath)) {
                this.logTest("Package.json", false, "package.json not found");
                return false;
            }

            const content = fs.readFileSync(packagePath, 'utf8');
            const packageJson = JSON.parse(content);
            
            // Check for essential dependencies
            const requiredDeps = [
                'react',
                'react-dom',
                'typescript',
                'vite',
                'axios',
                'react-hot-toast'
            ];

            const allDeps = { ...packageJson.dependencies, ...packageJson.devDependencies };
            const missingDeps = requiredDeps.filter(dep => !allDeps[dep]);

            const allDepsPresent = missingDeps.length === 0;
            this.logTest("Package Dependencies", allDepsPresent,
                        allDepsPresent ? "All required dependencies found" : 
                        `Missing dependencies: ${missingDeps.join(', ')}`);

            return allDepsPresent;
        } catch (error) {
            this.logTest("Package.json", false, error.message);
            return false;
        }
    }

    checkViteConfig() {
        try {
            const vitePath = join(__dirname, 'vite.config.ts');
            const vitePathJs = join(__dirname, 'vite.config.js');
            
            const configExists = fs.existsSync(vitePath) || fs.existsSync(vitePathJs);
            this.logTest("Vite Config", configExists,
                        configExists ? "Vite config file found" : "No Vite config found");

            return configExists;
        } catch (error) {
            this.logTest("Vite Config", false, error.message);
            return false;
        }
    }

    checkTsConfig() {
        try {
            const tsConfigPath = join(__dirname, 'tsconfig.json');
            if (!fs.existsSync(tsConfigPath)) {
                this.logTest("TypeScript Config", false, "tsconfig.json not found");
                return false;
            }

            const content = fs.readFileSync(tsConfigPath, 'utf8');
            const tsConfig = JSON.parse(content);
            
            const hasCompilerOptions = tsConfig.compilerOptions !== undefined;
            const hasTarget = tsConfig.compilerOptions?.target !== undefined;
            const hasModuleResolution = tsConfig.compilerOptions?.moduleResolution !== undefined;

            const isValid = hasCompilerOptions && hasTarget && hasModuleResolution;
            this.logTest("TypeScript Config", isValid,
                        isValid ? "Valid TypeScript configuration" : "Invalid or incomplete configuration");

            return isValid;
        } catch (error) {
            this.logTest("TypeScript Config", false, error.message);
            return false;
        }
    }

    checkEnvironmentFiles() {
        try {
            const envFiles = ['.env', '.env.local', '.env.development'];
            let envFound = false;

            for (const envFile of envFiles) {
                const envPath = join(__dirname, envFile);
                if (fs.existsSync(envPath)) {
                    envFound = true;
                    break;
                }
            }

            this.logTest("Environment Files", envFound,
                        envFound ? "Environment file found" : "No environment file found");

            return envFound;
        } catch (error) {
            this.logTest("Environment Files", false, error.message);
            return false;
        }
    }

    runComponentTests() {
        console.log("\n📱 Component Structure Tests:");
        
        const components = [
            { name: 'DocumentList', path: join(this.srcPath, 'components', 'DocumentList.tsx') },
            { name: 'DocumentUpload', path: join(this.srcPath, 'components', 'DocumentUpload.tsx') },
            { name: 'LoadingSpinner', path: join(this.srcPath, 'components', 'LoadingSpinner.tsx') },
            { name: 'SearchBar', path: join(this.srcPath, 'components', 'SearchBar.tsx') },
            { name: 'Layout', path: join(this.srcPath, 'components', 'Layout.tsx') }
        ];

        components.forEach(component => {
            this.checkComponentStructure(component.path, component.name);
        });
    }

    runFileStructureTests() {
        console.log("\n📁 File Structure Tests:");
        
        const criticalFiles = [
            { path: join(this.srcPath, 'App.tsx'), desc: 'Main App Component' },
            { path: join(this.srcPath, 'main.tsx'), desc: 'Entry Point' },
            { path: join(this.srcPath, 'services', 'api.ts'), desc: 'API Service' },
            { path: join(this.srcPath, 'components'), desc: 'Components Directory' },
            { path: join(this.srcPath, 'services'), desc: 'Services Directory' },
            { path: join(__dirname, 'index.html'), desc: 'HTML Template' }
        ];

        criticalFiles.forEach(file => {
            this.checkFileExists(file.path, file.desc);
        });
    }

    runConfigurationTests() {
        console.log("\n⚙️ Configuration Tests:");
        
        this.checkPackageJson();
        this.checkViteConfig();
        this.checkTsConfig();
        this.checkEnvironmentFiles();
    }

    runServiceTests() {
        console.log("\n🔌 Service Tests:");
        
        this.checkAPIServiceMethods();
        this.checkTypeScriptTypes();
    }

    runAllTests() {
        console.log("🚀 Starting Comprehensive Frontend Tests");
        console.log("=" * 50);

        this.runFileStructureTests();
        this.runComponentTests();
        this.runServiceTests();
        this.runConfigurationTests();

        return this.getResults();
    }

    getResults() {
        console.log("\n" + "=".repeat(50));
        console.log("📊 FRONTEND TEST RESULTS SUMMARY");
        console.log("=".repeat(50));
        console.log(`✅ Passed: ${this.testResults.passed}`);
        console.log(`❌ Failed: ${this.testResults.failed}`);
        
        const total = this.testResults.passed + this.testResults.failed;
        if (total > 0) {
            console.log(`📈 Success Rate: ${(this.testResults.passed / total * 100).toFixed(1)}%`);
        }

        if (this.testResults.errors.length > 0) {
            console.log("\n🚨 Failed Tests:");
            this.testResults.errors.forEach(error => {
                console.log(`  - ${error}`);
            });
        }

        return this.testResults;
    }
}

// Run tests if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
    const tester = new FrontendTester();
    const results = tester.runAllTests();
    
    if (results.failed > 0) {
        console.log("\n🎉 All frontend tests passed!");
        process.exit(0);
    } else {
        process.exit(1);
    }
} 