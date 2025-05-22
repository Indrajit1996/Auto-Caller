import { CircularProgress, Table, TableBody, TableCell, TablePagination, TableRow } from '@mui/material';
import { styled } from '@mui/material/styles';



import EnhancedTableHead from './EnhancedTableHead';





const REDUCED_FONT_SIZE = '0.875rem';
const CompactTableRow = styled(TableRow)(({ theme }) => ({
  '& > *': {
    padding: theme.spacing(1), // Reduce padding (vertical, horizontal)
  },
}));

const CompactTableCell = styled(TableCell)(({ theme }) => ({
  padding: theme.spacing(1), // Consistent with the row styling
  height: 'auto', // Allow the cell to shrink with content
  // Add ellipsis to overflow text
  whiteSpace: 'nowrap',
  overflow: 'hidden',
  textOverflow: 'ellipsis',

  '&:first-child': {
    paddingLeft: theme.spacing(2), // Larger padding for first cell
  },
  '&:last-child': {
    paddingRight: theme.spacing(2), // Larger padding for last cell
  },

  // Style icon buttons
  '& .MuiIconButton-root': {
    padding: 4, // Even smaller padding for icon buttons
  },

  // Make chips smaller too for consistency
  '& .MuiChip-root': {
    height: 24,
  },
  '& .MuiChip-label': {
    paddingLeft: 8,
    paddingRight: 8,
  },

  // don't show subtitle in list item text
  '& .MuiListItemText-secondary': {
    display: 'none',
  },

  '& .MuiListItemText-primary': {
    fontSize: REDUCED_FONT_SIZE,
  },
}));

const NormalTableRow = styled(TableRow)(({ theme }) => ({
  '& > *': {
    padding: theme.spacing(1.5, 2), // Default padding (vertical, horizontal)
  },
}));

const DataTable = ({
  loading,
  data,
  filteredColumns,
  order,
  orderBy,
  handleRequestSort,
  page,
  rowsPerPage,
  totalCount,
  handlePageChange,
  handleChangeRowsPerPage,
  getFilterContext,
  compact = false, // Option to use compact rows or not
}) => {
  const renderCell = (column, row) => {
    if (column.render) {
      const currentFilters = getFilterContext();
      return column.render(row, currentFilters);
    }
    return row[column.id] || '';
  };

  // Choose which components to use based on compact prop
  const RowComponent = compact ? CompactTableRow : NormalTableRow;
  const CellComponent = compact ? CompactTableCell : TableCell;

  return (
    <>
      <Table>
        <EnhancedTableHead
          columns={filteredColumns}
          order={order}
          orderBy={orderBy}
          onRequestSort={handleRequestSort}
        />
        <TableBody>
          {loading ? (
            <RowComponent>
              <CellComponent colSpan={filteredColumns.length} align='center'>
                <CircularProgress />
              </CellComponent>
            </RowComponent>
          ) : data.length === 0 ? (
            <RowComponent>
              <CellComponent colSpan={filteredColumns.length} align='center'>
                No data available
              </CellComponent>
            </RowComponent>
          ) : (
            data.map((row, index) => (
              <RowComponent key={index}>
                {filteredColumns.map((column) => (
                  <CellComponent key={column.id} align={column.align}>
                    {renderCell(column, row)}
                  </CellComponent>
                ))}
              </RowComponent>
            ))
          )}
        </TableBody>
      </Table>
      <TablePagination
        rowsPerPageOptions={[5, 10, 15, 25, 50]}
        component='div'
        count={totalCount}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handlePageChange}
        onRowsPerPageChange={handleChangeRowsPerPage}
        disabled={loading}
      />
    </>
  );
};

export default DataTable;