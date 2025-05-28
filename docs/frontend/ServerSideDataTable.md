# ServerSideDataTable Component

A comprehensive server-side data table component with built-in pagination, sorting, and search functionality.

## Features

- Server-side pagination
- Sortable columns
- Search functionality with debounce
- Loading states
- Empty state handling
- Customizable row actions
- Configurable rows per page

## Props

| Prop               | Type           | Description                              |
| ------------------ | -------------- | ---------------------------------------- |
| data               | Object[]       | Data to display in the table             |
| columns            | ColumnConfig[] | Column configurations                    |
| totalCount         | number         | Total number of records (for pagination) |
| onFetch            | function       | Callback for fetching data               |
| defaultSort        | Object         | Default sorting configuration            |
| defaultRowsPerPage | number         | Default number of rows per page          |
| loading            | boolean        | Loading state of the table               |

## Usage Example

```javascript
const columns = [
  {
    id: "name",
    label: "Name",
    sortable: true,
  },
  {
    id: "email",
    label: "Email",
    sortable: true,
  },
  {
    id: "status",
    label: "Status",
    sortable: true,
    render: (row) => <Chip label={row.status} />,
  },
];
<ServerSideDataTable
  data={users}
  columns={columns}
  totalCount={100}
  onFetch={(page, rowsPerPage, orderBy, order, search) => {
    fetchUsers({ page, rowsPerPage, orderBy, order, search });
  }}
  defaultSort={{ order: "desc", orderBy: "created_at" }}
  defaultRowsPerPage={10}
  loading={loading}
/>;
```

## Column Configuration

```javascript
{
id: string, // Unique identifier for the column
label: string, // Display label
sortable: boolean, // Whether column is sortable
align?: string, // Text alignment
width?: number|string, // Column width
render?: (row) => ReactNode // Custom render function for cell content
}
```

## Search Functionality

- Built-in search field with debounce (500ms)
- Clear search button
- Search icon indicator

## Pagination Features

- Configurable rows per page (5, 10, 25, 50)
- Page navigation
- Total count display
- Disabled state during loading
