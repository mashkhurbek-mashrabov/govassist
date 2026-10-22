import js from "@eslint/js";
import jsdoc from "eslint-plugin-jsdoc";
import jsxA11y from "eslint-plugin-jsx-a11y";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import globals from "globals";
import tseslint from "typescript-eslint";

/** ESLint flat config: TS strict rules, hooks, a11y and mandatory TSDoc (AGENTS.md → Code standards). */
export default tseslint.config(
  {
    ignores: [
      "dist",
      "dist-mock",
      "coverage",
      "public/mockServiceWorker.js",
      "playwright-report",
      "test-results",
    ],
  },
  {
    files: ["**/*.{ts,tsx}"],
    extends: [js.configs.recommended, ...tseslint.configs.strictTypeChecked, jsxA11y.flatConfigs.strict],
    languageOptions: {
      ecmaVersion: 2023,
      globals: { ...globals.browser, ...globals.node },
      parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname },
    },
    plugins: { "react-hooks": reactHooks, "react-refresh": reactRefresh, jsdoc },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "react-refresh/only-export-components": ["error", { allowConstantExport: true }],
      "@typescript-eslint/restrict-template-expressions": ["error", { allowNumber: true }],
      "@typescript-eslint/no-confusing-void-expression": ["error", { ignoreArrowShorthand: true }],
      "@typescript-eslint/no-unused-vars": ["error", { ignoreRestSiblings: true }],
      "no-console": ["error", { allow: ["info", "warn", "error"] }],
      "no-restricted-syntax": [
        "error",
        {
          selector: "JSXAttribute[name.name='dangerouslySetInnerHTML']",
          message: "Render text as plain text only (AGENTS.md → Security).",
        },
      ],
      "jsdoc/require-jsdoc": [
        "error",
        {
          publicOnly: false,
          require: {
            FunctionDeclaration: true,
            MethodDefinition: true,
            ClassDeclaration: true,
            ArrowFunctionExpression: false,
            FunctionExpression: false,
          },
          contexts: ["VariableDeclaration > VariableDeclarator > ArrowFunctionExpression"],
          checkConstructors: false,
        },
      ],
    },
  },
  {
    files: ["**/*.test.{ts,tsx}", "e2e/**", "src/test/**", "src/mocks/**", "scripts/**"],
    rules: { "react-refresh/only-export-components": "off" },
  },
);
