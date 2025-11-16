const nextJest = require('next/jest')

const createJestConfig = nextJest({
  dir: './frontend/bs_reviews',
})

const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/frontend/bs_reviews/$1',
  },
  testMatch: [
    '<rootDir>/tests/frontend/**/*.test.tsx',
    '<rootDir>/tests/frontend/**/*.test.ts',
  ],
  modulePaths: ['<rootDir>/frontend/bs_reviews'],
  roots: ['<rootDir>/tests', '<rootDir>/frontend/bs_reviews'],
  moduleDirectories: ['node_modules', '<rootDir>/node_modules', '<rootDir>/frontend/bs_reviews/node_modules'],
}

module.exports = createJestConfig(customJestConfig)