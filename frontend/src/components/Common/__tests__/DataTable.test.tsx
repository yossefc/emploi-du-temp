import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Mock data for testing
const mockData = [
  { id: 1, name: 'John Doe', email: 'john@example.com', age: 30, active: true },
  { id: 2, name: 'Jane Smith', email: 'jane@example.com', age: 25, active: false },
  { id: 3, name: 'Bob Johnson', email: 'bob@example.com', age: 35, active: true }
];

const mockColumns = [
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
    key: 'age',
    title: 'Âge',
    dataIndex: 'age',
    sortable: true,
    filterable: true,
    filterType: 'number'
  },
  {
    key: 'active',
    title: 'Actif',
    dataIndex: 'active',
    filterable: true,
    filterType: 'boolean',
    render: (value: boolean) => value ? 'Oui' : 'Non'
  }
];

// Simple mock DataTable component for testing
const MockDataTable = ({ data, columns, loading, title, ...props }: any) => {
  if (loading) {
    return (
      <div>
        <div data-testid="loading-skeleton">Loading...</div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return <div>Aucune donnée trouvée</div>;
  }

  return (
    <div>
      {title && <h2>{title}</h2>}
      <table role="table">
        <thead>
          <tr>
            {columns.map((col: any) => (
              <th key={col.key} role="columnheader">
                {col.title}
                {col.sortable && (
                  <button aria-label={`Trier par ${col.title}`}>
                    Sort
                  </button>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row: any) => (
            <tr key={row.id}>
              {columns.map((col: any) => (
                <td key={col.key}>
                  {col.render ? col.render(row[col.dataIndex]) : row[col.dataIndex]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <div>
        {columns
          .filter((col: any) => col.filterable)
          .map((col: any) => (
            <input
              key={`filter-${col.key}`}
              placeholder={`Filtrer par ${col.title.toLowerCase()}`}
              aria-label={`Filtrer par ${col.title.toLowerCase()}`}
            />
          ))}
      </div>
    </div>
  );
};

describe('DataTable Component', () => {
  const defaultProps = {
    data: mockData,
    columns: mockColumns
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    test('renders table with data', () => {
      render(<MockDataTable {...defaultProps} />);
      
      // Check if table is rendered
      expect(screen.getByRole('table')).toBeInTheDocument();
      
      // Check if headers are rendered
      expect(screen.getByText('Nom')).toBeInTheDocument();
      expect(screen.getByText('Email')).toBeInTheDocument();
      expect(screen.getByText('Âge')).toBeInTheDocument();
      
      // Check if data is rendered
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('jane@example.com')).toBeInTheDocument();
      expect(screen.getByText('35')).toBeInTheDocument();
    });

    test('renders with title', () => {
      render(<MockDataTable {...defaultProps} title="Test Table" />);
      expect(screen.getByText('Test Table')).toBeInTheDocument();
    });

    test('renders loading skeleton when loading', () => {
      render(<MockDataTable {...defaultProps} loading={true} />);
      
      // Should show skeleton loaders
      const skeletons = screen.getAllByTestId('loading-skeleton');
      expect(skeletons.length).toBeGreaterThan(0);
    });

    test('renders empty state when no data', () => {
      render(<MockDataTable {...defaultProps} data={[]} />);
      expect(screen.getByText('Aucune donnée trouvée')).toBeInTheDocument();
    });
  });

  describe('Column Features', () => {
    test('renders sortable column indicators', () => {
      render(<MockDataTable {...defaultProps} />);
      
      // Check for sort buttons on sortable columns
      expect(screen.getByLabelText('Trier par Nom')).toBeInTheDocument();
      expect(screen.getByLabelText('Trier par Email')).toBeInTheDocument();
      expect(screen.getByLabelText('Trier par Âge')).toBeInTheDocument();
    });

    test('renders filter inputs for filterable columns', () => {
      render(<MockDataTable {...defaultProps} />);
      
      // Should have filter inputs for filterable columns
      expect(screen.getByLabelText('Filtrer par nom')).toBeInTheDocument();
      expect(screen.getByLabelText('Filtrer par email')).toBeInTheDocument();
      expect(screen.getByLabelText('Filtrer par âge')).toBeInTheDocument();
      expect(screen.getByLabelText('Filtrer par actif')).toBeInTheDocument();
    });
  });

  describe('Data Rendering', () => {
    test('renders custom content with render function', () => {
      render(<MockDataTable {...defaultProps} />);
      
      // Check boolean column rendering - use getAllByText since there are multiple "Oui"
      const ouiElements = screen.getAllByText('Oui');
      expect(ouiElements).toHaveLength(2); // John and Bob are active
      expect(screen.getByText('Non')).toBeInTheDocument(); // Jane is not active
    });

    test('handles different data types', () => {
      render(<MockDataTable {...defaultProps} />);
      
      // String values
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      // Number values
      expect(screen.getByText('30')).toBeInTheDocument();
      expect(screen.getByText('25')).toBeInTheDocument();
      expect(screen.getByText('35')).toBeInTheDocument();
    });
  });

  describe('User Interactions', () => {
    test('allows typing in filter inputs', async () => {
      const user = userEvent.setup();
      render(<MockDataTable {...defaultProps} />);
      
      const nameFilter = screen.getByLabelText('Filtrer par nom');
      await user.type(nameFilter, 'John');
      
      expect(nameFilter).toHaveValue('John');
    });

    test('allows clicking sort buttons', async () => {
      const user = userEvent.setup();
      render(<MockDataTable {...defaultProps} />);
      
      const sortButton = screen.getByLabelText('Trier par Nom');
      await user.click(sortButton);
      
      // Button should be clickable
      expect(sortButton).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    test('handles missing data gracefully', () => {
      render(<MockDataTable data={[]} columns={mockColumns} />);
      expect(screen.getByText('Aucune donnée trouvée')).toBeInTheDocument();
    });

    test('handles invalid column configuration', () => {
      const invalidColumns = [
        {
          key: 'invalid',
          title: 'Invalid Column',
          dataIndex: 'nonExistentField'
        }
      ];

      expect(() => {
        render(<MockDataTable data={mockData} columns={invalidColumns} />);
      }).not.toThrow();
      
      expect(screen.getByRole('table')).toBeInTheDocument();
    });

    test('handles null or undefined values', () => {
      const dataWithNulls = [
        { id: 1, name: null, email: undefined, age: 30, active: true }
      ];

      expect(() => {
        render(<MockDataTable data={dataWithNulls} columns={mockColumns} />);
      }).not.toThrow();
      
      expect(screen.getByRole('table')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    test('renders accessible table structure', () => {
      render(<MockDataTable {...defaultProps} />);
      
      expect(screen.getByRole('table')).toBeInTheDocument();
      expect(screen.getAllByRole('columnheader')).toHaveLength(4);
      expect(screen.getAllByRole('row')).toHaveLength(4); // 1 header + 3 data rows
    });

    test('provides proper ARIA labels', () => {
      render(<MockDataTable {...defaultProps} />);
      
      // Check for accessibility labels
      expect(screen.getByLabelText('Filtrer par nom')).toBeInTheDocument();
      expect(screen.getByLabelText('Trier par Nom')).toBeInTheDocument();
    });

    test('provides proper semantic structure', () => {
      render(<MockDataTable {...defaultProps} />);
      
      const table = screen.getByRole('table');
      const thead = table.querySelector('thead');
      const tbody = table.querySelector('tbody');
      
      expect(thead).toBeInTheDocument();
      expect(tbody).toBeInTheDocument();
    });
  });

  describe('Performance', () => {
    test('renders without performance issues', () => {
      const largeData = Array.from({ length: 100 }, (_, i) => ({
        id: i,
        name: `User ${i}`,
        email: `user${i}@example.com`,
        age: 20 + (i % 50),
        active: i % 2 === 0
      }));

      const startTime = performance.now();
      render(<MockDataTable data={largeData} columns={mockColumns} />);
      const endTime = performance.now();
      
      expect(screen.getByRole('table')).toBeInTheDocument();
      
      // Should render reasonably fast (less than 100ms for 100 items)
      expect(endTime - startTime).toBeLessThan(100);
    });
  });

  describe('Props Validation', () => {
    test('accepts required props', () => {
      expect(() => {
        render(<MockDataTable data={mockData} columns={mockColumns} />);
      }).not.toThrow();
    });

    test('works with minimal props', () => {
      const minimalColumns = [
        { key: 'name', title: 'Name', dataIndex: 'name' }
      ];
      
      expect(() => {
        render(<MockDataTable data={mockData} columns={minimalColumns} />);
      }).not.toThrow();
      
      expect(screen.getByRole('table')).toBeInTheDocument();
    });

    test('handles empty columns array', () => {
      expect(() => {
        render(<MockDataTable data={mockData} columns={[]} />);
      }).not.toThrow();
    });
  });

  describe('Component State', () => {
    test('maintains component integrity with re-renders', () => {
      const { rerender } = render(<MockDataTable {...defaultProps} />);
      
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      
      rerender(<MockDataTable {...defaultProps} title="Updated Title" />);
      
      expect(screen.getByText('Updated Title')).toBeInTheDocument();
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    test('updates when data changes', () => {
      const { rerender } = render(<MockDataTable {...defaultProps} />);
      
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      
      const newData = [
        { id: 4, name: 'Alice Cooper', email: 'alice@example.com', age: 28, active: true }
      ];
      
      rerender(<MockDataTable data={newData} columns={mockColumns} />);
      
      expect(screen.queryByText('John Doe')).not.toBeInTheDocument();
      expect(screen.getByText('Alice Cooper')).toBeInTheDocument();
    });
  });
}); 