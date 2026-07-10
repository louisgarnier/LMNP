const nextJest = require('next/jest');

// Fournit le chemin vers l'app Next.js pour charger next.config.js et .env dans l'environnement de test
const createJestConfig = nextJest({
  dir: './',
});

// Config Jest personnalisée
const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
};

// createJestConfig est exporté de cette façon pour garantir que next/jest peut charger la config Next.js (async)
module.exports = createJestConfig(customJestConfig);
