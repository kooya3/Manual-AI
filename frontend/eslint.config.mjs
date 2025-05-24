import { dirname } from "path";
import { fileURLToPath } from "url";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

const eslintConfig = [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    rules: {
      // Disable all TypeScript strict checking
      "@typescript-eslint/no-explicit-any": "off",
      "@typescript-eslint/no-unused-vars": "off",
      "@typescript-eslint/explicit-function-return-type": "off",
      "@typescript-eslint/no-empty-function": "off",
      "@typescript-eslint/no-non-null-assertion": "off",
      // Disable React rules
      "react/prop-types": "off",
      "react/react-in-jsx-scope": "off",
      // Disable other common rules
      "no-unused-vars": "off",
      "no-console": "off",
      "no-undef": "warn",
      // Turn all other rules to warnings
      ...Object.keys(eslintConfig.rules || {}).reduce(
        (acc, key) => ({
          ...acc,
          [key]: "warn",
        }),
        {}
      ),
    },
    // Ignore all TypeScript errors during build
    parserOptions: {
      project: null,
    },
  },
];

export default eslintConfig;
