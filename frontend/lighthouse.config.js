module.exports = {
  // Configuration pour les audits Lighthouse automatisés
  ci: {
    collect: {
      url: [
        'http://localhost:3000/',
        'http://localhost:3000/subjects',
        'http://localhost:3000/teachers',
        'http://localhost:3000/class-groups',
        'http://localhost:3000/rooms',
        'http://localhost:3000/timetable',
      ],
      numberOfRuns: 3,
      settings: {
        chromeFlags: '--no-sandbox --headless --disable-gpu',
        preset: 'desktop',
        throttling: {
          rttMs: 40,
          throughputKbps: 10240,
          cpuSlowdownMultiplier: 1,
          requestLatencyMs: 0,
          downloadThroughputKbps: 0,
          uploadThroughputKbps: 0,
        },
        skipAudits: [
          // Skip audits that don't apply to SPAs
          'canonical',
          'robots-txt',
          'structured-data',
        ],
      },
    },
    assert: {
      assertions: {
        // Performance budgets
        'categories:performance': ['error', { minScore: 0.9 }],
        'categories:accessibility': ['error', { minScore: 0.95 }],
        'categories:best-practices': ['error', { minScore: 0.9 }],
        'categories:seo': ['warn', { minScore: 0.8 }],
        'categories:pwa': ['off'],

        // Core Web Vitals
        'first-contentful-paint': ['error', { maxNumericValue: 1800 }],
        'largest-contentful-paint': ['error', { maxNumericValue: 2500 }],
        'first-input-delay': ['error', { maxNumericValue: 100 }],
        'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }],
        'speed-index': ['warn', { maxNumericValue: 3000 }],
        'total-blocking-time': ['warn', { maxNumericValue: 300 }],

        // Accessibility specific
        'color-contrast': 'error',
        'document-title': 'error',
        'html-has-lang': 'error',
        'image-alt': 'error',
        'label': 'error',
        'link-name': 'error',
        'list': 'error',
        'meta-description': 'warn',
        'meta-viewport': 'error',

        // Performance specific
        'unused-javascript': ['warn', { maxNumericValue: 300000 }], // 300KB
        'unused-css-rules': ['warn', { maxNumericValue: 20000 }], // 20KB
        'uses-responsive-images': 'warn',
        'uses-webp-images': 'warn',
        'efficient-animated-content': 'warn',
        'preload-lcp-image': 'warn',
        'uses-text-compression': 'error',

        // Best practices
        'uses-https': 'error',
        'uses-http2': 'warn',
        'no-vulnerable-libraries': 'error',
        'csp-xss': 'warn',
        'is-on-https': 'error',

        // Bundle size budgets
        'resource-summary:script:size': ['warn', { maxNumericValue: 1048576 }], // 1MB JS
        'resource-summary:stylesheet:size': ['warn', { maxNumericValue: 102400 }], // 100KB CSS
        'resource-summary:image:size': ['warn', { maxNumericValue: 2097152 }], // 2MB images
        'resource-summary:total:size': ['warn', { maxNumericValue: 3145728 }], // 3MB total
      },
    },
    upload: {
      target: 'temporary-public-storage',
    },
  },

  // Configuration pour les audits en développement
  extends: 'lighthouse:default',
  settings: {
    onlyAudits: [
      // Performance
      'first-contentful-paint',
      'largest-contentful-paint',
      'first-meaningful-paint',
      'speed-index',
      'interactive',
      'first-cpu-idle',
      'max-potential-fid',
      'cumulative-layout-shift',
      'total-blocking-time',

      // Accessibility
      'color-contrast',
      'document-title',
      'html-has-lang',
      'image-alt',
      'label',
      'link-name',
      'list',
      'listitem',
      'meta-description',
      'meta-viewport',
      'heading-order',
      'duplicate-id-active',
      'duplicate-id-aria',
      'valid-lang',
      'aria-allowed-attr',
      'aria-hidden-body',
      'aria-hidden-focus',
      'aria-input-field-name',
      'aria-required-attr',
      'aria-required-children',
      'aria-required-parent',
      'aria-roles',
      'aria-toggle-field-name',
      'aria-valid-attr-value',
      'aria-valid-attr',
      'button-name',
      'bypass',
      'definition-list',
      'dlitem',
      'focus-traps',
      'focusable-controls',
      'form-field-multiple-labels',
      'frame-title',
      'input-image-alt',
      'keyboard',
      'landmark-one-main',
      'logical-tab-order',
      'managed-focus',
      'object-alt',
      'tabindex',
      'td-headers-attr',
      'th-has-data-cells',
      'use-landmarks',
      'visual-order-follows-dom',

      // Best practices
      'uses-https',
      'uses-http2',
      'uses-passive-event-listeners',
      'no-document-write',
      'external-anchors-use-rel-noopener',
      'geolocation-on-start',
      'doctype',
      'no-vulnerable-libraries',
      'notification-on-start',
      'password-inputs-can-be-pasted-into',
      'uses-http2',
      'uses-passive-event-listeners',

      // SEO
      'document-title',
      'meta-description',
      'http-status-code',
      'link-text',
      'is-crawlable',
      'robots-txt',
      'image-alt',
      'hreflang',
      'canonical',

      // PWA (optionnel)
      'service-worker',
      'offline-start-url',
      'works-offline',
      'viewport',
      'without-javascript',
      'apple-touch-icon',
      'themed-omnibox',
      'content-width',
      'themed-omnibox',
    ],

    // Configuration mobile
    formFactor: 'mobile',
    throttling: {
      rttMs: 150,
      throughputKbps: 1638.4,
      requestLatencyMs: 562.5,
      downloadThroughputKbps: 1638.4,
      uploadThroughputKbps: 675,
      cpuSlowdownMultiplier: 4,
    },
    screenEmulation: {
      mobile: true,
      width: 412,
      height: 823,
      deviceScaleFactor: 2.625,
      disabled: false,
    },
    emulatedUserAgent: 'Mozilla/5.0 (Linux; Android 7.0; Moto G (4)) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.87 Mobile Safari/537.36',
  },

  // Catégories personnalisées pour l'école
  categories: {
    performance: {
      title: 'Performance',
      auditRefs: [
        { id: 'first-contentful-paint', weight: 10, group: 'metrics' },
        { id: 'largest-contentful-paint', weight: 25, group: 'metrics' },
        { id: 'first-meaningful-paint', weight: 10, group: 'metrics' },
        { id: 'speed-index', weight: 10, group: 'metrics' },
        { id: 'interactive', weight: 10, group: 'metrics' },
        { id: 'first-cpu-idle', weight: 5, group: 'metrics' },
        { id: 'max-potential-fid', weight: 10, group: 'metrics' },
        { id: 'cumulative-layout-shift', weight: 15, group: 'metrics' },
        { id: 'total-blocking-time', weight: 30, group: 'metrics' },
      ],
    },
    accessibility: {
      title: 'Accessibilité',
      description: 'Conformité WCAG 2.1 AA pour l\'application scolaire',
      auditRefs: [
        { id: 'color-contrast', weight: 3, group: 'a11y-color-contrast' },
        { id: 'document-title', weight: 3, group: 'a11y-names-labels' },
        { id: 'html-has-lang', weight: 3, group: 'a11y-language' },
        { id: 'image-alt', weight: 10, group: 'a11y-names-labels' },
        { id: 'label', weight: 10, group: 'a11y-names-labels' },
        { id: 'link-name', weight: 3, group: 'a11y-names-labels' },
        { id: 'button-name', weight: 10, group: 'a11y-names-labels' },
        { id: 'focus-traps', weight: 3, group: 'a11y-keyboard' },
        { id: 'focusable-controls', weight: 3, group: 'a11y-keyboard' },
        { id: 'keyboard', weight: 3, group: 'a11y-keyboard' },
        { id: 'logical-tab-order', weight: 3, group: 'a11y-keyboard' },
        { id: 'managed-focus', weight: 3, group: 'a11y-keyboard' },
        { id: 'use-landmarks', weight: 3, group: 'a11y-navigation' },
        { id: 'bypass', weight: 3, group: 'a11y-navigation' },
      ],
    },
    'school-specific': {
      title: 'Spécifique École',
      description: 'Critères spécifiques pour une application de gestion scolaire',
      auditRefs: [
        { id: 'uses-text-compression', weight: 1 },
        { id: 'unused-javascript', weight: 1 },
        { id: 'unused-css-rules', weight: 1 },
        { id: 'efficient-animated-content', weight: 1 },
        { id: 'preload-lcp-image', weight: 1 },
      ],
    },
  },

  // Groups pour organiser les audits
  groups: {
    metrics: {
      title: 'Métriques',
    },
    'load-opportunities': {
      title: 'Opportunités d\'optimisation',
    },
    'a11y-keyboard': {
      title: 'Navigation clavier',
    },
    'a11y-names-labels': {
      title: 'Noms et étiquettes',
    },
    'a11y-color-contrast': {
      title: 'Contraste des couleurs',
    },
    'a11y-language': {
      title: 'Langue',
    },
    'a11y-navigation': {
      title: 'Navigation',
    },
  },
};