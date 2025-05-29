/** .eslintrc.js - ESLint configuration (✨ added) */
module.exports = {
    parser: '@typescript-eslint/parser',
    parserOptions: {
        ecmaVersion: 2021,
        sourceType: 'module',
        ecmaFeatures: { jsx: true },
    },
    env: {
        browser: true,
        es2021: true,
        node: true,
    },
    plugins: ['react', '@typescript-eslint'],
    extends: [
        'eslint:recommended',
        'plugin:react/recommended',
        'plugin:@typescript-eslint/recommended',
        'prettier',
    ],
    settings: {
        react: { version: 'detect' }, // Automatically detect React version
    },
    rules: {
        // Add custom rules or overrides if needed (currently using recommended rules)
    },
};
