import '@testing-library/jest-dom'

// Global test configuration
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock window.scrollTo
Object.defineProperty(window, 'scrollTo', {
  value: vi.fn(),
  writable: true
})

// Mock HTMLElement.scrollIntoView
HTMLElement.prototype.scrollIntoView = vi.fn()

// Mock crypto for test environment
Object.defineProperty(window, 'crypto', {
  value: {
    getRandomValues: vi.fn(() => new Uint32Array(1))
  }
}) 