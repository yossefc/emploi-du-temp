import React from 'react';
import { render, screen, RenderOptions } from '@testing-library/react';
import { configureAxe } from 'jest-axe';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { NotificationProvider } from '../contexts/NotificationContext';

// Configure jest-axe
const axe = configureAxe({
  rules: {
    // Disable certain rules that may not be relevant for testing
    'color-contrast': { enabled: false },
  },
});

// Mock global objects that might not be available in the test environment
global.IntersectionObserver = class IntersectionObserver {
  root: Element | null = null;
  rootMargin: string = '';
  thresholds: ReadonlyArray<number> = [];
  
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
  takeRecords(): IntersectionObserverEntry[] { return []; }
} as any;

global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
} as any;

// Mock window methods
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
});

// Mock scrollTo
Object.defineProperty(window, 'scrollTo', {
  value: vi.fn(),
  writable: true
});

// Mock crypto for testing
Object.defineProperty(window, 'crypto', {
  value: {
    getRandomValues: vi.fn().mockImplementation((array: any) => {
      for (let i = 0; i < array.length; i++) {
        array[i] = Math.floor(Math.random() * 256);
      }
      return array;
    })
  }
});

// Setup providers for testing
interface AllTheProvidersProps {
  children: React.ReactNode;
}

const AllTheProviders: React.FC<AllTheProvidersProps> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: Infinity,
      },
      mutations: {
        retry: false,
      },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <NotificationProvider>
          {children}
        </NotificationProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

// Custom render function
const customRender = (
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => {
  return render(ui, { wrapper: AllTheProviders, ...options });
};

// Accessibility testing utilities
export const testAccessibility = async (container: HTMLElement) => {
  const results = await axe(container);
  expect(results).toHaveNoViolations();
  return results;
};

export const testKeyboardNavigation = async (element: HTMLElement) => {
  const user = userEvent.setup();
  
  // Test focus
  await user.tab();
  expect(element).toHaveFocus();
  
  // Test activation with keyboard
  await user.keyboard('{Enter}');
  await user.keyboard(' ');
  
  return true;
};

export const testScreenReaderSupport = (element: HTMLElement) => {
  // Check for ARIA attributes
  const ariaLabel = element.getAttribute('aria-label');
  const ariaLabelledBy = element.getAttribute('aria-labelledby');
  const ariaDescribedBy = element.getAttribute('aria-describedby');
  const role = element.getAttribute('role');
  
  const hasAccessibleName = ariaLabel || ariaLabelledBy || element.textContent;
  
  return {
    hasAccessibleName: !!hasAccessibleName,
    hasRole: !!role,
    hasDescription: !!ariaDescribedBy,
    ariaAttributes: {
      label: ariaLabel,
      labelledBy: ariaLabelledBy,
      describedBy: ariaDescribedBy,
      role,
    },
  };
};

export const testColorContrast = async (element: HTMLElement) => {
  const styles = window.getComputedStyle(element);
  const color = styles.color;
  const backgroundColor = styles.backgroundColor;
  
  // Note: In a real implementation, you'd use a library like 'color-contrast'
  // to calculate the actual contrast ratio
  return {
    color,
    backgroundColor,
    hasContrast: color !== backgroundColor,
  };
};

// Performance testing utilities
export const measureRenderTime = async (renderFn: () => void) => {
  const start = performance.now();
  renderFn();
  const end = performance.now();
  return end - start;
};

export const testLargeDataset = <T,>(
  Component: React.ComponentType<{ data: T[] }>,
  dataGenerator: (count: number) => T[],
  itemCount = 1000
) => {
  const data = dataGenerator(itemCount);
  const renderTime = measureRenderTime(() => {
    customRender(<Component data={data} />);
  });
  
  expect(renderTime).toBeLessThan(1000); // Should render in less than 1 second
  return renderTime;
};

// Mock data generators
export const generateMockSubjects = (count: number) => {
  return Array.from({ length: count }, (_, i) => ({
    id: i + 1,
    name: `Subject ${i + 1}`,
    name_ar: `مادة ${i + 1}`,
    code: `SUB${String(i + 1).padStart(3, '0')}`,
    description: `Description for subject ${i + 1}`,
    description_ar: `وصف المادة ${i + 1}`,
    hours_per_week: Math.floor(Math.random() * 6) + 1,
    is_active: Math.random() > 0.1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }));
};

export const generateMockTeachers = (count: number) => {
  return Array.from({ length: count }, (_, i) => ({
    id: i + 1,
    first_name: `Teacher${i + 1}`,
    first_name_ar: `أستاذ${i + 1}`,
    last_name: `Last${i + 1}`,
    last_name_ar: `الأخير${i + 1}`,
    email: `teacher${i + 1}@school.com`,
    phone: `+1234567${String(i).padStart(3, '0')}`,
    specialization: `Specialization ${i + 1}`,
    specialization_ar: `تخصص ${i + 1}`,
    hire_date: new Date().toISOString().split('T')[0],
    is_active: Math.random() > 0.1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }));
};

export const generateMockClassGroups = (count: number) => {
  return Array.from({ length: count }, (_, i) => ({
    id: i + 1,
    name: `Class ${i + 1}`,
    name_ar: `صف ${i + 1}`,
    level: Math.floor(Math.random() * 12) + 1,
    section: String.fromCharCode(65 + (i % 26)),
    academic_year: '2023-2024',
    max_students: Math.floor(Math.random() * 15) + 25,
    current_students: Math.floor(Math.random() * 30) + 20,
    is_active: Math.random() > 0.1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }));
};

export const generateMockRooms = (count: number) => {
  return Array.from({ length: count }, (_, i) => ({
    id: i + 1,
    name: `Room ${i + 1}`,
    name_ar: `قاعة ${i + 1}`,
    type: ['classroom', 'laboratory', 'library', 'auditorium'][Math.floor(Math.random() * 4)],
    capacity: Math.floor(Math.random() * 30) + 20,
    floor: Math.floor(Math.random() * 4) + 1,
    building: `Building ${Math.floor(Math.random() * 3) + 1}`,
    building_ar: `مبنى ${Math.floor(Math.random() * 3) + 1}`,
    equipment: ['projector', 'whiteboard', 'computers'],
    is_active: Math.random() > 0.1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }));
};

// Async testing utilities
export const waitForElementToBeRemoved = async (element: HTMLElement) => {
  return new Promise<void>((resolve) => {
    const observer = new MutationObserver(() => {
      if (!document.contains(element)) {
        observer.disconnect();
        resolve();
      }
    });
    
    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });
  });
};

export const waitForLoadingToFinish = async () => {
  // Wait for loading indicators to disappear
  await screen.findByRole('progressbar').catch(() => {}); // Ignore if not found
  const progressbar = screen.queryByRole('progressbar');
  if (progressbar) {
    await waitForElementToBeRemoved(progressbar).catch(() => {});
  }
};

// Form testing utilities
export const fillForm = async (formData: Record<string, string>) => {
  const user = userEvent.setup();
  
  for (const [fieldName, value] of Object.entries(formData)) {
    const field = screen.getByLabelText(new RegExp(fieldName, 'i'));
    await user.clear(field);
    await user.type(field, value);
  }
};

export const submitForm = async () => {
  const user = userEvent.setup();
  const submitButton = screen.getByRole('button', { name: /submit|save|create|update/i });
  await user.click(submitButton);
};

// Visual regression testing setup
export const setupVisualRegression = () => {
  // Mock implementation for visual regression testing
  // In a real implementation, you'd use tools like Percy, Chromatic, or jest-image-snapshot
  return {
    takeSnapshot: (name: string) => {
      console.log(`Taking visual snapshot: ${name}`);
    },
  };
};

// Error boundary for testing
export const TestErrorBoundary: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div data-testid="error-boundary">
      {children}
    </div>
  );
};

export const triggerError = () => {
  throw new Error('Test error for error boundary');
};

// Hook testing utilities - simplified version to avoid complex generic typing
// @ts-ignore - Complex generic constraints with testing library - known issue
export const renderHook = <TResult,>(
  hook: () => TResult
) => {
  const result = { current: null as TResult | null };
  
  const HookComponent = () => {
    result.current = hook();
    return null;
  };

  const { rerender, unmount } = customRender(<HookComponent />);

  return {
    result,
    rerender: () => rerender(<HookComponent />),
    unmount,
  };
};

// Export everything
export {
  customRender as render,
  AllTheProviders,
  axe,
};

// Re-export testing library utilities
export * from '@testing-library/react';
export { userEvent }; 