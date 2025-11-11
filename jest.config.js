module.exports = {
  testMatch: ['**/static/js/**/?(*.)+(spec|test).js'],
  testEnvironment: 'jsdom',
  collectCoverageFrom: [
    'static/js/**/*.js',
    '!static/js/__tests__/**',
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov'],
};
