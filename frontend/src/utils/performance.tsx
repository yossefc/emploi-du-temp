import React, { useEffect, useRef, useCallback, useState } from 'react';

// Types for performance monitoring
export interface PerformanceMetrics {
  fcp: number; // First Contentful Paint
  lcp: number; // Largest Contentful Paint
  fid: number; // First Input Delay
  cls: number; // Cumulative Layout Shift
  ttfb: number; // Time To First Byte
  memoryUsage?: number;
  jsHeapSize?: number;
}

export interface ComponentPerformance {
  componentName: string;
  renderTime: number;
  rerenderCount: number;
  propsChanges: number;
}

// Performance-focused cache implementation
export class PerformanceCache<T = any> {
  private cache = new Map<string, { value: T; timestamp: number; hits: number }>();
  private readonly maxSize: number;
  private readonly ttl: number;

  constructor(maxSize = 100, ttlMinutes = 30) {
    this.maxSize = maxSize;
    this.ttl = ttlMinutes * 60 * 1000;
  }

  get(key: string): T | null {
    const entry = this.cache.get(key);
    
    if (!entry) {
      return null;
    }

    // Check if expired
    if (Date.now() - entry.timestamp > this.ttl) {
      this.cache.delete(key);
      return null;
    }

    // Update hit count and timestamp
    entry.hits++;
    entry.timestamp = Date.now();
    
    return entry.value;
  }

  set(key: string, value: T): void {
    // Check if cache is full
    if (this.cache.size >= this.maxSize && !this.cache.has(key)) {
      this.evictLeastUsed();
    }

    this.cache.set(key, {
      value,
      timestamp: Date.now(),
      hits: 0,
    });
  }

  has(key: string): boolean {
    return this.cache.has(key) && this.get(key) !== null;
  }

  delete(key: string): void {
    this.cache.delete(key);
  }

  clear(): void {
    this.cache.clear();
  }

  invalidateByPattern(pattern: RegExp): void {
    for (const key of this.cache.keys()) {
      if (pattern.test(key)) {
        this.cache.delete(key);
      }
    }
  }

  private evictLeastUsed(): void {
    let leastUsedKey: string | null = null;
    let leastHits = Infinity;

    for (const [key, entry] of this.cache.entries()) {
      if (entry.hits < leastHits) {
        leastHits = entry.hits;
        leastUsedKey = key;
      }
    }

    if (leastUsedKey) {
      this.cache.delete(leastUsedKey);
    }
  }

  getStats() {
    return {
      size: this.cache.size,
      maxSize: this.maxSize,
      hitRate: this.calculateHitRate(),
      memoryEstimate: this.estimateMemoryUsage(),
      oldestEntry: this.getOldestEntry(),
    };
  }

  private calculateHitRate(): number {
    let totalHits = 0;
    let totalAccesses = 0;

    for (const entry of this.cache.values()) {
      totalHits += entry.hits;
      totalAccesses += entry.hits + 1; // +1 for initial set
    }

    return totalAccesses > 0 ? totalHits / totalAccesses : 0;
  }

  private getOldestEntry(): number {
    let oldest = Date.now();

    for (const entry of this.cache.values()) {
      if (entry.timestamp < oldest) {
        oldest = entry.timestamp;
      }
    }

    return oldest;
  }

  private estimateMemoryUsage(): number {
    // Rough estimation of memory usage in bytes
    let totalSize = 0;

    for (const [key, entry] of this.cache.entries()) {
      // Estimate key size (2 bytes per character for UTF-16)
      totalSize += key.length * 2;
      
      // Estimate value size (rough approximation)
      totalSize += JSON.stringify(entry.value).length * 2;
      
      // Add overhead for object structure
      totalSize += 64; // Rough estimate for object overhead
    }

    return totalSize;
  }
}

// Debounce hook for performance optimization
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

// Throttle hook for performance optimization
export function useThrottle<T>(value: T, limit: number): T {
  const [throttledValue, setThrottledValue] = useState<T>(value);
  const lastRan = useRef<number>(Date.now());

  useEffect(() => {
    const handler = setTimeout(() => {
      if (Date.now() - lastRan.current >= limit) {
        setThrottledValue(value);
        lastRan.current = Date.now();
      }
    }, limit - (Date.now() - lastRan.current));

    return () => {
      clearTimeout(handler);
    };
  }, [value, limit]);

  return throttledValue;
}

// Intersection Observer hook for lazy loading
export function useIntersectionObserver(
  options: IntersectionObserverInit = {}
): [React.RefCallback<Element>, boolean] {
  const [isIntersecting, setIsIntersecting] = useState(false);
  const [element, setElement] = useState<Element | null>(null);

  const ref = useCallback((node: Element | null) => {
    setElement(node);
  }, []);

  useEffect(() => {
    if (!element) return;

    const observer = new IntersectionObserver(([entry]) => {
      setIsIntersecting(entry.isIntersecting);
    }, options);

    observer.observe(element);

    return () => {
      observer.disconnect();
    };
  }, [element, options]);

  return [ref, isIntersecting];
}

// Virtual list hook for large datasets
export function useVirtualList<T>({
  items,
  itemHeight,
  containerHeight,
  overscan = 5,
}: {
  items: T[];
  itemHeight: number;
  containerHeight: number;
  overscan?: number;
}) {
  const [scrollTop, setScrollTop] = useState(0);

  const visibleItemCount = Math.ceil(containerHeight / itemHeight);
  const startIndex = Math.floor(scrollTop / itemHeight);
  const endIndex = Math.min(startIndex + visibleItemCount + overscan, items.length);

  const visibleItems = items.slice(
    Math.max(0, startIndex - overscan),
    endIndex
  );

  const totalHeight = items.length * itemHeight;
  const offsetY = Math.max(0, startIndex - overscan) * itemHeight;

  const onScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  }, []);

  return {
    visibleItems,
    totalHeight,
    offsetY,
    onScroll,
    startIndex: Math.max(0, startIndex - overscan),
    endIndex,
  };
}

// Main performance monitor class
export class PerformanceMonitor {
  private static instance: PerformanceMonitor;
  private metrics: PerformanceMetrics[] = [];
  private componentMetrics = new Map<string, ComponentPerformance>();

  static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor();
    }
    return PerformanceMonitor.instance;
  }

  startMeasure(name: string): void {
    performance.mark(`${name}-start`);
  }

  endMeasure(name: string): number {
    performance.mark(`${name}-end`);
    performance.measure(name, `${name}-start`, `${name}-end`);
    const measure = performance.getEntriesByName(name, 'measure')[0];
    return measure.duration;
  }

  recordComponentRender(componentName: string, renderTime: number): void {
    const existing = this.componentMetrics.get(componentName);
    
    if (existing) {
      existing.renderTime = (existing.renderTime + renderTime) / 2; // Average
      existing.rerenderCount++;
    } else {
      this.componentMetrics.set(componentName, {
        componentName,
        renderTime,
        rerenderCount: 1,
        propsChanges: 0,
      });
    }
  }

  recordPropsChange(componentName: string): void {
    const existing = this.componentMetrics.get(componentName);
    if (existing) {
      existing.propsChanges++;
    }
  }

  getCoreWebVitals(): Promise<PerformanceMetrics> {
    return new Promise((resolve) => {
      const metrics: Partial<PerformanceMetrics> = {};

      // FCP - First Contentful Paint
      if ('PerformanceObserver' in window) {
        const fcpObserver = new PerformanceObserver((entryList) => {
          const entries = entryList.getEntries();
          const fcpEntry = entries.find(entry => entry.name === 'first-contentful-paint');
          if (fcpEntry) {
            metrics.fcp = fcpEntry.startTime;
          }
          fcpObserver.disconnect();
        });

        try {
          fcpObserver.observe({ entryTypes: ['paint'] });
        } catch (e) {
          // FCP not supported
        }
      }

      // LCP - Largest Contentful Paint
      if ('PerformanceObserver' in window) {
        const lcpObserver = new PerformanceObserver((entryList) => {
          const entries = entryList.getEntries();
          const lastEntry = entries[entries.length - 1];
          metrics.lcp = lastEntry.startTime;
          lcpObserver.disconnect();
        });

        try {
          lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
        } catch (e) {
          // LCP not supported
        }
      }

      // FID - First Input Delay
      if ('PerformanceObserver' in window) {
        const fidObserver = new PerformanceObserver((entryList) => {
          for (const entry of entryList.getEntries()) {
            if (entry.entryType === 'first-input') {
              metrics.fid = (entry as any).processingStart - entry.startTime;
              fidObserver.disconnect();
              break;
            }
          }
        });

        try {
          fidObserver.observe({ entryTypes: ['first-input'] });
        } catch (e) {
          // FID not supported
        }
      }

      // CLS - Cumulative Layout Shift
      if ('PerformanceObserver' in window) {
        let clsValue = 0;
        const clsObserver = new PerformanceObserver((entryList) => {
          for (const entry of entryList.getEntries()) {
            if (!(entry as any).hadRecentInput) {
              clsValue += (entry as any).value;
            }
          }
          metrics.cls = clsValue;
        });

        try {
          clsObserver.observe({ entryTypes: ['layout-shift'] });
        } catch (e) {
          // CLS not supported
        }
      }

      // TTFB - Time To First Byte
      const navigationEntry = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      if (navigationEntry) {
        metrics.ttfb = navigationEntry.responseStart - navigationEntry.fetchStart;
      }

      // Memory usage
      if ('memory' in performance) {
        const memInfo = (performance as any).memory;
        metrics.memoryUsage = memInfo.usedJSHeapSize;
        metrics.jsHeapSize = memInfo.totalJSHeapSize;
      }

      // Wait a bit for all observers to trigger
      setTimeout(() => {
        resolve(metrics as PerformanceMetrics);
      }, 1000);
    });
  }

  getComponentMetrics(): ComponentPerformance[] {
    return Array.from(this.componentMetrics.values());
  }

  clearMetrics(): void {
    this.metrics = [];
    this.componentMetrics.clear();
    performance.clearMarks();
    performance.clearMeasures();
  }

  exportMetrics(): string {
    return JSON.stringify({
      coreWebVitals: this.metrics,
      componentMetrics: this.getComponentMetrics(),
      timestamp: new Date().toISOString(),
    }, null, 2);
  }
}

// Hook to measure component performance
export function useComponentPerformance(componentName: string) {
  const monitor = PerformanceMonitor.getInstance();
  const renderStartRef = useRef<number>();
  const propsHashRef = useRef<string>();

  const startRender = useCallback(() => {
    renderStartRef.current = performance.now();
  }, []);

  const endRender = useCallback(() => {
    if (renderStartRef.current) {
      const renderTime = performance.now() - renderStartRef.current;
      monitor.recordComponentRender(componentName, renderTime);
    }
  }, [componentName, monitor]);

  const recordPropsChange = useCallback((props: any) => {
    const propsHash = JSON.stringify(props);
    if (propsHashRef.current && propsHashRef.current !== propsHash) {
      monitor.recordPropsChange(componentName);
    }
    propsHashRef.current = propsHash;
  }, [componentName, monitor]);

  useEffect(() => {
    startRender();
    return endRender;
  });

  return { recordPropsChange };
}

// Code splitting utilities with proper JSX
export const lazy = <T extends React.ComponentType<any>>(
  factory: () => Promise<{ default: T }>,
  fallback?: React.ComponentType
) => {
  const LazyComponent = React.lazy(factory);
  
  // @ts-ignore - Complex generic forwardRef constraint with lazy components
  return React.forwardRef<T, React.ComponentProps<T>>((props, ref) => {
    const FallbackComponent = fallback;
    return (
      <React.Suspense fallback={FallbackComponent ? <FallbackComponent /> : <div>Loading...</div>}>
        {/* @ts-ignore - Generic constraint issue with lazy components */}
        <LazyComponent {...props} ref={ref} />
      </React.Suspense>
    );
  });
};

// Preload utilities
export const preloadRoute = (routeComponent: () => Promise<any>) => {
  const componentImport = routeComponent();
  return componentImport;
};

export const preloadComponent = (component: () => Promise<any>) => {
  // Preload on mouseover/focus for better UX
  return {
    onMouseEnter: () => component(),
    onFocus: () => component(),
  };
};

// Resource hints
export const addResourceHint = (href: string, as: string, type: 'preload' | 'prefetch' = 'preload') => {
  const link = document.createElement('link');
  link.rel = type;
  link.href = href;
  link.as = as;
  document.head.appendChild(link);
};

// Performance budget checker
export const checkPerformanceBudget = (metrics: PerformanceMetrics) => {
  const budgets = {
    fcp: 1800, // 1.8s
    lcp: 2500, // 2.5s
    fid: 100,  // 100ms
    cls: 0.1,  // 0.1
    ttfb: 600, // 600ms
  };

  const violations: string[] = [];

  Object.entries(budgets).forEach(([metric, budget]) => {
    const metricValue = metrics[metric as keyof PerformanceMetrics];
    if (metricValue !== undefined && metricValue > budget) {
      violations.push(`${metric.toUpperCase()}: ${metricValue}ms > ${budget}ms`);
    }
  });

  return {
    passed: violations.length === 0,
    violations,
    score: Math.max(0, 100 - violations.length * 20),
  };
};

export default PerformanceMonitor; 