import {
  Box,
  Button,
  Checkbox,
  Divider,
  Fade,
  FormControlLabel,
  FormGroup,
  Popover,
  Typography,
  useTheme,
} from '@mui/material';

const ColumnVisibilityPopover = ({
  columnMenuAnchorEl,
  handleColumnMenuClose,
  columns,
  visibleColumns,
  toggleColumnVisibility,
  resetColumnVisibility,
  filteredColumns,
}) => {
  const theme = useTheme();
  return (
    <Popover
      id='column-menu'
      open={Boolean(columnMenuAnchorEl)}
      anchorEl={columnMenuAnchorEl}
      onClose={handleColumnMenuClose}
      anchorOrigin={{
        vertical: 'bottom',
        horizontal: 'right',
      }}
      transformOrigin={{
        vertical: 'top',
        horizontal: 'right',
      }}
      TransitionComponent={Fade}
      slotProps={{
        paper: {
          sx: {
            width: '15rem',
            maxWidth: '100%',
            mt: 1,
            overflowY: 'auto',
            maxHeight: '40vh',
            borderRadius: 1,
            boxShadow: theme.shadows[3],
          },
        },
      }}
    >
      <Box p={2}>
        <Typography variant='subtitle1' fontWeight='bold'>
          Column Visibility
        </Typography>
      </Box>
      <Divider style={{ marginBottom: 12 }} />
      <Box px={2}>
        <FormGroup>
          {columns.map((column) => (
            <FormControlLabel
              key={column.id}
              control={
                <Checkbox
                  checked={visibleColumns[column.id]}
                  onChange={() => toggleColumnVisibility(column.id)}
                  size='small'
                  color='primary'
                  disabled={filteredColumns.length === 1 && visibleColumns[column.id]}
                />
              }
              label={column.label}
            />
          ))}
        </FormGroup>
      </Box>
      <Divider style={{ marginTop: 12 }} />

      <Box p={2}>
        <Button size='small' onClick={resetColumnVisibility} variant='outlined' fullWidth>
          Restore Default
        </Button>
      </Box>
    </Popover>
  );
};

export default ColumnVisibilityPopover;
