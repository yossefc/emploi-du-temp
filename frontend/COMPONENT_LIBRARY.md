# Bibliothèque de Composants Réutilisables

Une collection de composants React avancés pour améliorer l'expérience utilisateur dans l'application d'emploi du temps.

## 🎯 Vue d'ensemble

Cette bibliothèque fournit des composants génériques hautement configurables et réutilisables :

- **DataTable** : Table de données avancée avec tri, filtres, pagination, sélection multiple et export
- **FormModal** : Modal de formulaire universelle avec validation, multi-étapes et auto-save
- **NotificationSystem** : Système de notifications avec priorités, actions et historique
- **ErrorBoundary** : Gestion d'erreurs avec fallback UI et reporting automatique
- **LoadingStates** : États de chargement contextuels avec skeleton loaders

## 📋 Table des Matières

1. [Installation](#installation)
2. [DataTable](#datatable)
3. [FormModal](#formmodal)
4. [NotificationSystem](#notificationsystem)
5. [ErrorHandling](#errorhandling)
6. [Hooks](#hooks)
7. [Patterns UX](#patterns-ux)
8. [Tests](#tests)
9. [Contribution](#contribution)

## 🚀 Installation

```bash
# Installer les dépendances
npm install @heroicons/react
npm install react react-dom

# Types pour TypeScript
npm install -D @types/react @types/react-dom
```

## 📊 DataTable

### Fonctionnalités

- ✅ Tri multi-colonnes avec indicateurs visuels
- ✅ Filtres par type (texte, nombre, date, booléen, sélection)
- ✅ Pagination avec tailles variables
- ✅ Sélection multiple avec actions groupées
- ✅ Export CSV/Excel/PDF intégré
- ✅ Colonnes redimensionnables et réorganisables
- ✅ État persistant (localStorage)
- ✅ Loading states avec skeleton
- ✅ États vides avec suggestions

### Utilisation Basique

```tsx
import DataTable, { ColumnConfig } from '@/components/Common/DataTable';

const columns: ColumnConfig[] = [
  {
    key: 'name',
    title: 'Nom',
    dataIndex: 'name',
    sortable: true,
    filterable: true,
    filterType: 'text'
  },
  {
    key: 'email',
    title: 'Email',
    dataIndex: 'email',
    sortable: true,
    filterable: true,
    filterType: 'text'
  },
  {
    key: 'status',
    title: 'Status',
    dataIndex: 'status',
    filterable: true,
    filterType: 'select',
    filterOptions: [
      { label: 'Actif', value: 'active' },
      { label: 'Inactif', value: 'inactive' }
    ],
    render: (value) => (
      <span className={`badge ${value === 'active' ? 'badge-success' : 'badge-danger'}`}>
        {value === 'active' ? 'Actif' : 'Inactif'}
      </span>
    )
  }
];

function UserTable() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  });

  return (
    <DataTable
      data={data}
      columns={columns}
      loading={loading}
      title="Gestion des Utilisateurs"
      pagination={{
        ...pagination,
        showSizeChanger: true,
        onChange: (page, pageSize) => {
          setPagination({ ...pagination, current: page, pageSize });
          // Fetch new data
        }
      }}
      rowSelection={{
        type: 'checkbox',
        selectedRowKeys: selectedUsers,
        onChange: (keys, rows) => setSelectedUsers(keys)
      }}
      actions={[
        {
          key: 'delete',
          label: 'Supprimer',
          type: 'danger',
          onClick: (selectedRows) => handleBulkDelete(selectedRows)
        },
        {
          key: 'export',
          label: 'Exporter sélection',
          onClick: (selectedRows) => handleExport(selectedRows)
        }
      ]}
      exportConfig={{
        filename: 'users-export',
        formats: ['csv', 'excel', 'pdf']
      }}
      persistState={true}
      stateKey="users-table"
    />
  );
}
```

### Configuration Avancée

```tsx
// Column avec rendu personnalisé
const advancedColumns: ColumnConfig[] = [
  {
    key: 'avatar',
    title: 'Avatar',
    dataIndex: 'avatar',
    render: (value, record) => (
      <img 
        src={value || '/default-avatar.png'} 
        alt={record.name}
        className="w-8 h-8 rounded-full"
      />
    ),
    width: 80,
    exportable: false
  },
  {
    key: 'actions',
    title: 'Actions',
    dataIndex: 'id',
    render: (id, record) => (
      <div className="flex space-x-2">
        <button onClick={() => editUser(id)}>
          <PencilIcon className="w-4 h-4" />
        </button>
        <button onClick={() => deleteUser(id)}>
          <TrashIcon className="w-4 h-4" />
        </button>
      </div>
    ),
    width: 100,
    exportable: false
  }
];

// Avec validation personnalisée et dépendances
const conditionalColumns: ColumnConfig[] = [
  {
    key: 'startDate',
    title: 'Date de début',
    dataIndex: 'startDate',
    filterType: 'date',
    validation: (value, allValues) => {
      if (value && allValues.endDate && new Date(value) > new Date(allValues.endDate)) {
        return 'La date de début doit être antérieure à la date de fin';
      }
      return '';
    }
  },
  {
    key: 'endDate',
    title: 'Date de fin',
    dataIndex: 'endDate',
    filterType: 'date',
    dependencies: ['startDate']
  }
];
```

### API Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `data` | `T[]` | `[]` | Données à afficher |
| `columns` | `ColumnConfig<T>[]` | `[]` | Configuration des colonnes |
| `loading` | `boolean` | `false` | État de chargement |
| `pagination` | `PaginationConfig` | - | Configuration pagination |
| `rowSelection` | `RowSelectionConfig` | - | Configuration sélection |
| `title` | `string` | - | Titre de la table |
| `actions` | `ActionConfig[]` | `[]` | Actions groupées |
| `exportConfig` | `ExportConfig` | - | Configuration export |
| `persistState` | `boolean` | `true` | Sauvegarde état |
| `stateKey` | `string` | `'dataTable'` | Clé de sauvegarde |

## 📝 FormModal

### Fonctionnalités

- ✅ Gestion automatique des états (create/edit/view/duplicate)
- ✅ Validation Yup/custom intégrée avec messages
- ✅ Auto-save des brouillons
- ✅ Progression multi-étapes
- ✅ Upload de fichiers avec preview et progress
- ✅ Dirty detection avec confirmation de sortie
- ✅ Mode responsive avec tailles configurables

### Utilisation Basique

```tsx
import FormModal, { FormField } from '@/components/Common/FormModal';

const userFields: FormField[] = [
  {
    name: 'firstName',
    label: 'Prénom',
    type: 'text',
    required: true,
    placeholder: 'Entrez le prénom'
  },
  {
    name: 'lastName',
    label: 'Nom',
    type: 'text',
    required: true,
    placeholder: 'Entrez le nom'
  },
  {
    name: 'email',
    label: 'Email',
    type: 'email',
    required: true,
    validation: async (value) => {
      const exists = await checkEmailExists(value);
      return exists ? 'Cet email est déjà utilisé' : '';
    }
  },
  {
    name: 'role',
    label: 'Rôle',
    type: 'select',
    required: true,
    options: [
      { label: 'Administrateur', value: 'admin' },
      { label: 'Professeur', value: 'teacher' },
      { label: 'Étudiant', value: 'student' }
    ]
  },
  {
    name: 'bio',
    label: 'Biographie',
    type: 'textarea',
    rows: 4,
    max: 500
  }
];

function UserModal() {
  const [isOpen, setIsOpen] = useState(false);
  const [mode, setMode] = useState<'create' | 'edit' | 'view'>('create');
  const [initialValues, setInitialValues] = useState({});

  const handleSubmit = async (values: any, currentMode: string) => {
    try {
      if (currentMode === 'create') {
        await createUser(values);
        notify.success('Utilisateur créé avec succès');
      } else {
        await updateUser(values.id, values);
        notify.success('Utilisateur modifié avec succès');
      }
      setIsOpen(false);
    } catch (error) {
      notify.error('Erreur lors de la sauvegarde');
    }
  };

  const handleDraft = (values: any) => {
    localStorage.setItem('user-draft', JSON.stringify(values));
  };

  return (
    <FormModal
      open={isOpen}
      onClose={() => setIsOpen(false)}
      title={mode === 'create' ? 'Nouvel Utilisateur' : 'Modifier Utilisateur'}
      mode={mode}
      fields={userFields}
      initialValues={initialValues}
      onSubmit={handleSubmit}
      onDraft={handleDraft}
      size="lg"
      autoSave={true}
      autoSaveInterval={30000}
      confirmBeforeClose={true}
      allowModeSwitch={true}
      customActions={[
        {
          key: 'sendEmail',
          label: 'Envoyer email de bienvenue',
          type: 'secondary',
          onClick: (values) => sendWelcomeEmail(values.email)
        }
      ]}
    />
  );
}
```

### Formulaire Multi-étapes

```tsx
const steps: FormStep[] = [
  {
    key: 'personal',
    title: 'Informations personnelles',
    description: 'Nom, prénom, email',
    fields: ['firstName', 'lastName', 'email', 'phone'],
    validation: async (values) => {
      const errors: Record<string, string> = {};
      if (!values.firstName?.trim()) {
        errors.firstName = 'Le prénom est requis';
      }
      return errors;
    }
  },
  {
    key: 'professional',
    title: 'Informations professionnelles',
    description: 'Poste, département, manager',
    fields: ['position', 'department', 'manager'],
    optional: false
  },
  {
    key: 'preferences',
    title: 'Préférences',
    description: 'Notifications, langue, thème',
    fields: ['notifications', 'language', 'theme'],
    optional: true
  }
];

<FormModal
  // ... autres props
  steps={steps}
  showProgress={true}
/>
```

### Upload de Fichiers

```tsx
const fileFields: FormField[] = [
  {
    name: 'avatar',
    label: 'Photo de profil',
    type: 'file',
    accept: 'image/*',
    multiple: false,
    validation: (value) => {
      if (value && value.size > 2 * 1024 * 1024) {
        return 'Le fichier ne doit pas dépasser 2MB';
      }
      return '';
    }
  },
  {
    name: 'documents',
    label: 'Documents',
    type: 'file',
    accept: '.pdf,.doc,.docx',
    multiple: true
  }
];
```

## 🔔 NotificationSystem

### Fonctionnalités

- ✅ Types de notifications (success, error, warning, info)
- ✅ Priorités (low, normal, high, urgent)
- ✅ Notifications persistantes
- ✅ Queue avec gestion hors ligne
- ✅ Actions inline (retry, dismiss, details)
- ✅ Historique consultable avec filtres
- ✅ Positions configurables

### Configuration

```tsx
import { NotificationProvider } from '@/components/Common/NotificationSystem';

function App() {
  return (
    <NotificationProvider
      maxNotifications={5}
      defaultDuration={5000}
      position="top-right"
    >
      <YourApp />
    </NotificationProvider>
  );
}
```

### Utilisation

```tsx
import { useNotifications } from '@/components/Common/NotificationSystem';

function MyComponent() {
  const { addNotification, toggleHistory } = useNotifications();

  const handleSuccess = () => {
    addNotification({
      type: 'success',
      title: 'Opération réussie',
      message: 'Les données ont été sauvegardées avec succès',
      priority: 'normal',
      autoHide: true,
      duration: 5000
    });
  };

  const handleError = () => {
    addNotification({
      type: 'error',
      title: 'Erreur de connexion',
      message: 'Impossible de se connecter au serveur',
      priority: 'high',
      persistent: true,
      actions: [
        {
          label: 'Réessayer',
          type: 'primary',
          onClick: () => retryConnection()
        },
        {
          label: 'Paramètres',
          type: 'secondary',
          onClick: () => openSettings()
        }
      ],
      onRetry: async () => {
        await retryConnection();
      },
      maxRetries: 3
    });
  };

  const handleWithRetry = () => {
    addNotification({
      type: 'warning',
      title: 'Sauvegarde en cours...',
      message: 'La sauvegarde prend plus de temps que prévu',
      priority: 'urgent',
      onRetry: async () => {
        try {
          await forceSave();
          // Mise à jour automatique vers success
          addNotification({
            type: 'success',
            title: 'Sauvegarde terminée',
            priority: 'normal'
          });
        } catch (error) {
          throw new Error('Échec de la sauvegarde forcée');
        }
      },
      retryCount: 0,
      maxRetries: 5
    });
  };

  return (
    <div>
      <button onClick={handleSuccess}>Succès</button>
      <button onClick={handleError}>Erreur</button>
      <button onClick={handleWithRetry}>Avec retry</button>
      <button onClick={toggleHistory}>Historique</button>
    </div>
  );
}
```

### Utilitaires notify

```tsx
import { notify } from '@/components/Common/NotificationSystem';

// Raccourcis pour utilisation rapide
notify.success('Opération réussie');
notify.error('Erreur critique', { 
  persistent: true,
  actions: [{ label: 'Support', onClick: () => openSupport() }]
});
notify.warning('Attention', { priority: 'high' });
notify.info('Information', { duration: 3000 });
```

## 🛡️ ErrorHandling

### ErrorBoundary

```tsx
import { ErrorBoundary } from '@/utils/errorHandling';

function App() {
  return (
    <ErrorBoundary
      enableReporting={true}
      showDetails={process.env.NODE_ENV === 'development'}
      onError={(errorInfo) => {
        console.log('Error caught:', errorInfo);
        // Envoyer à votre service de monitoring
      }}
      fallback={(errorInfo) => (
        <CustomErrorPage errorInfo={errorInfo} />
      )}
    >
      <YourApp />
    </ErrorBoundary>
  );
}
```

### ErrorHandler Utilitaire

```tsx
import { ErrorHandler } from '@/utils/errorHandling';

// Gestion d'erreur réseau avec retry
const fetchData = async () => {
  try {
    const response = await fetch('/api/data');
    if (!response.ok) throw new Error('Network error');
    return response.json();
  } catch (error) {
    ErrorHandler.handleNetworkError(error, {
      retry: fetchData,
      maxRetries: 3,
      retryDelay: 1000
    });
  }
};

// Gestion d'erreur de validation
const validateForm = (data) => {
  const errors = {};
  if (!data.email) errors.email = 'Email requis';
  if (Object.keys(errors).length > 0) {
    ErrorHandler.handleValidationError(errors, { formData: data });
  }
};

// Gestion d'erreur de permission
const accessResource = () => {
  if (!user.hasPermission('read:users')) {
    ErrorHandler.handlePermissionError('lecture', 'utilisateurs');
  }
};
```

### Hook useErrorHandler

```tsx
import { useErrorHandler } from '@/utils/errorHandling';

function MyComponent() {
  const { 
    handleError, 
    handleNetworkError, 
    handleValidationError 
  } = useErrorHandler();

  const submit = async (data) => {
    try {
      await api.post('/users', data);
    } catch (error) {
      if (error.name === 'ValidationError') {
        handleValidationError(error.details);
      } else if (error.name === 'NetworkError') {
        handleNetworkError(error, {
          retry: () => submit(data),
          maxRetries: 3
        });
      } else {
        handleError(error, { component: 'UserForm' });
      }
    }
  };
}
```

## 🎣 Hooks

### useTable

Gestion complète de l'état d'une table de données.

```tsx
import { useTable } from '@/hooks/useTable';

const {
  tableData,        // Données filtrées et triées
  sortConfig,       // Configuration tri actuel
  filters,          // Filtres actifs
  selectedRows,     // Lignes sélectionnées
  columnWidths,     // Largeurs colonnes
  columnOrder,      // Ordre colonnes
  hiddenColumns,    // Colonnes masquées
  handleSort,       // Fonction tri
  handleFilter,     // Fonction filtre
  exportData,       // Fonction export
  resetFilters,     // Reset filtres
  saveState,        // Sauvegarde état
  loadState         // Chargement état
} = useTable({
  data,
  columns,
  rowSelection,
  persistState: true,
  stateKey: 'my-table'
});
```

### useForm

Gestion d'état et validation de formulaires.

```tsx
import { useForm } from '@/hooks/useForm';

const {
  values,           // Valeurs actuelles
  errors,           // Erreurs de validation
  touched,          // Champs touchés
  isDirty,          // Formulaire modifié
  isSubmitting,     // Soumission en cours
  handleChange,     // Gestion changement
  handleBlur,       // Gestion focus
  handleSubmit,     // Soumission
  setFieldValue,    // Définir valeur champ
  setFieldError,    // Définir erreur champ
  validateField,    // Valider champ
  validateForm,     // Valider formulaire
  resetForm,        // Reset formulaire
  getFieldProps     // Props pour binding
} = useForm({
  initialValues,
  fields,
  onSubmit,
  validationMode: 'onBlur'
});
```

## 🎨 Patterns UX

### Loading States

```tsx
// Skeleton Loader
function SkeletonLoader({ rows = 5 }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="animate-pulse">
          <div className="flex space-x-4">
            <div className="rounded-full bg-gray-200 h-10 w-10"></div>
            <div className="flex-1 space-y-2 py-1">
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// Progress Bar
function ProgressBar({ progress, message }) {
  return (
    <div className="w-full">
      <div className="flex justify-between mb-1">
        <span className="text-sm font-medium text-gray-700">{message}</span>
        <span className="text-sm text-gray-500">{progress}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div 
          className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
```

### Empty States

```tsx
function EmptyState({ 
  icon, 
  title, 
  description, 
  action 
}) {
  return (
    <div className="text-center py-12">
      <div className="text-gray-300 mb-4">
        {icon || <DocumentIcon className="mx-auto h-12 w-12" />}
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-2">
        {title}
      </h3>
      <p className="text-gray-500 mb-6">
        {description}
      </p>
      {action && (
        <button
          onClick={action.onClick}
          className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
        >
          {action.icon && <span className="mr-2">{action.icon}</span>}
          {action.label}
        </button>
      )}
    </div>
  );
}
```

## 🧪 Tests

### Configuration Jest

```javascript
// setupTests.js
import '@testing-library/jest-dom';

// Mock des APIs du navigateur
Object.defineProperty(window, 'localStorage', {
  value: {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
    clear: jest.fn(),
  },
  writable: true,
});

global.fetch = jest.fn();
```

### Tests de Composants

```tsx
// DataTable.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DataTable from '../DataTable';

describe('DataTable', () => {
  const mockData = [
    { id: 1, name: 'John', email: 'john@example.com' }
  ];

  const mockColumns = [
    { key: 'name', title: 'Nom', dataIndex: 'name', sortable: true }
  ];

  test('renders data correctly', () => {
    render(<DataTable data={mockData} columns={mockColumns} />);
    expect(screen.getByText('John')).toBeInTheDocument();
  });

  test('handles sorting', async () => {
    const mockHandleSort = jest.fn();
    render(
      <DataTable 
        data={mockData} 
        columns={mockColumns}
        onSort={mockHandleSort}
      />
    );
    
    await userEvent.click(screen.getByText('Nom'));
    expect(mockHandleSort).toHaveBeenCalledWith('name', 'asc');
  });
});
```

### Tests de Hooks

```tsx
// useForm.test.tsx
import { renderHook, act } from '@testing-library/react';
import { useForm } from '../useForm';

describe('useForm', () => {
  const mockFields = [
    { name: 'email', type: 'email', required: true }
  ];

  test('validates required fields', async () => {
    const { result } = renderHook(() => 
      useForm({ 
        initialValues: {}, 
        fields: mockFields,
        onSubmit: jest.fn()
      })
    );

    await act(async () => {
      await result.current.validateField('email', '');
    });

    expect(result.current.errors.email).toBe('Email est requis');
  });
});
```

## 📈 Performance

### Optimisations

```tsx
// Mémoisation des colonnes
const columns = useMemo(() => [
  { key: 'name', title: 'Nom', dataIndex: 'name' }
], []);

// Callback stable pour actions
const handleDelete = useCallback((ids: string[]) => {
  // Logic here
}, []);

// Virtualisation pour grandes listes
import { FixedSizeList as List } from 'react-window';

function VirtualizedTable({ data }) {
  const Row = ({ index, style }) => (
    <div style={style}>
      {/* Row content */}
    </div>
  );

  return (
    <List
      height={400}
      itemCount={data.length}
      itemSize={50}
    >
      {Row}
    </List>
  );
}
```

### Lazy Loading

```tsx
// Composants lazy
const DataTable = lazy(() => import('./DataTable'));
const FormModal = lazy(() => import('./FormModal'));

// Avec Suspense
function App() {
  return (
    <Suspense fallback={<SkeletonLoader />}>
      <DataTable {...props} />
    </Suspense>
  );
}
```

## 🎯 Bonnes Pratiques

### Structure des Fichiers

```
src/
├── components/
│   └── Common/
│       ├── DataTable.tsx
│       ├── FormModal.tsx
│       ├── NotificationSystem.tsx
│       └── __tests__/
├── hooks/
│   ├── useTable.ts
│   ├── useForm.ts
│   └── __tests__/
├── utils/
│   ├── errorHandling.ts
│   └── __tests__/
└── types/
    ├── table.ts
    ├── form.ts
    └── notification.ts
```

### Conventions de Nommage

```tsx
// Props avec préfixe explicite
interface DataTableProps {
  tableData: any[];
  tableColumns: ColumnConfig[];
  tablePagination?: PaginationConfig;
}

// Handlers avec préfixe handle
const handleTableSort = (key: string) => {};
const handleFormSubmit = (values: any) => {};
const handleNotificationDismiss = (id: string) => {};

// États avec suffixe State si ambiguïté
const [loadingState, setLoadingState] = useState(false);
const [errorState, setErrorState] = useState(null);
```

### Accessibilité

```tsx
// Labels et ARIA
<button
  aria-label="Trier par nom"
  aria-describedby="sort-help"
  onClick={handleSort}
>
  Nom
</button>

// Focus management
const focusRef = useRef<HTMLButtonElement>(null);

useEffect(() => {
  if (isOpen) {
    focusRef.current?.focus();
  }
}, [isOpen]);

// Keyboard navigation
const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' || e.key === ' ') {
    handleAction();
  }
};
```

## 🔧 Configuration Avancée

### Thème Personnalisé

```tsx
// theme.ts
export const theme = {
  colors: {
    primary: '#4f46e5',
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
    info: '#3b82f6'
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem'
  },
  borderRadius: {
    sm: '0.125rem',
    md: '0.375rem',
    lg: '0.5rem'
  }
};

// Utilisation
<DataTable
  className="custom-table"
  style={{
    '--primary-color': theme.colors.primary,
    '--border-radius': theme.borderRadius.md
  }}
/>
```

### Intégration avec React Query

```tsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

function UserTable() {
  const queryClient = useQueryClient();
  
  const { data, isLoading, error } = useQuery({
    queryKey: ['users'],
    queryFn: fetchUsers
  });

  const deleteMutation = useMutation({
    mutationFn: deleteUsers,
    onSuccess: () => {
      queryClient.invalidateQueries(['users']);
      notify.success('Utilisateurs supprimés');
    },
    onError: (error) => {
      notify.error('Erreur lors de la suppression');
    }
  });

  return (
    <DataTable
      data={data || []}
      loading={isLoading}
      actions={[
        {
          key: 'delete',
          label: 'Supprimer',
          type: 'danger',
          onClick: (selectedRows) => {
            deleteMutation.mutate(selectedRows.map(r => r.id));
          }
        }
      ]}
    />
  );
}
```

## 🤝 Contribution

### Guidelines

1. **Tests** : Tous les nouveaux composants doivent avoir une couverture de tests ≥ 80%
2. **Documentation** : Chaque prop et méthode doit être documentée
3. **TypeScript** : Types stricts requis, pas de `any`
4. **Accessibilité** : Respect des standards WCAG 2.1 AA
5. **Performance** : Mémoisation appropriée et éviter les re-renders inutiles

### Scripts de Développement

```bash
# Tests
npm run test
npm run test:watch
npm run test:coverage

# Linting
npm run lint
npm run lint:fix

# Build
npm run build
npm run build:analyze

# Storybook
npm run storybook
npm run build-storybook
```

### Process de Review

1. Fork du repository
2. Création d'une branche feature
3. Développement avec tests
4. Pull Request avec description détaillée
5. Review par au moins 2 développeurs
6. Merge après approbation

## 📚 Ressources

- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Headless UI](https://headlessui.dev/) - Composants accessibles
- [Tailwind CSS](https://tailwindcss.com/) - Framework CSS
- [React Hook Form](https://react-hook-form.com/) - Alternative pour formulaires
- [React Query](https://tanstack.com/query) - Gestion état serveur

---

## 🏷️ Changelog

### v1.0.0 (2024-01-XX)
- ✨ Initial release
- ✨ DataTable avec toutes fonctionnalités
- ✨ FormModal multi-étapes
- ✨ NotificationSystem complet
- ✨ ErrorBoundary et gestion d'erreurs
- ✨ Tests complets et documentation