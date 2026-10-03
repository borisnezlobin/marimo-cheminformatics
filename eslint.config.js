export default [
  {
    files: ["game/*.js", "widgets/clash.js"],
    ignores: ["game/assets.js"],
    languageOptions: { ecmaVersion: 2023, sourceType: "script" },
    rules: { complexity: ["error", 15] },
  },
  {
    files: ["widgets/clash.js"],
    languageOptions: { sourceType: "module" },
  },
];
