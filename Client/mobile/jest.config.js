module.exports = {
  preset: "jest-expo",
  testMatch: ["**/*.test.ts", "**/*.test.tsx"],
  setupFilesAfterEnv: ["<rootDir>/jest.setup.js"],
  moduleNameMapper: {
    "^react-native/setup-env$": "<rootDir>/jest.setup.js",
    "^test-renderer$": "react-test-renderer",
    "^@/(.*)$": "<rootDir>/src/$1",
  },
  transformIgnorePatterns: [
    "node_modules/(?!((jest-)?react-native|@react-native(-community)?)|expo(nent)?|@expo(nent)?/.*|@expo-google-fonts/.*|react-navigation|@react-navigation/.*|@sentry/react-native|nativewind|react-native-css-interop|zustand)",
  ],
};
