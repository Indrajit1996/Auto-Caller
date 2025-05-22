import {
  Box,
  Divider,
  FormControl,
  FormLabel,
  Grid2 as Grid,
  Popover,
  Typography,
  useTheme,
} from '@mui/material';

import { renderFilterInput } from './utils';

const FilterPopover = ({
  isFilterOpen,
  filterAnchorEl,
  handleCloseFilters,
  filters,
  filterValues,
  handleFilterChange,
}) => {
  const theme = useTheme();
  return (
    <Popover
      id='filter-popover'
      open={isFilterOpen}
      anchorEl={filterAnchorEl}
      onClose={handleCloseFilters}
      anchorOrigin={{
        vertical: 'bottom',
        horizontal: 'right',
      }}
      transformOrigin={{
        vertical: 'top',
        horizontal: 'right',
      }}
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
          Filters
        </Typography>
      </Box>
      <Divider style={{ marginBottom: 12 }} />
      <Grid container spacing={2.5} sx={{ p: 2 }}>
        {filters.map((filter) => (
          <Grid size={12} key={filter.id}>
            <FormLabel
              sx={{
                display: 'block',
                mb: 0.5,
                color: 'text.primary',
              }}
            >
              <Typography variant='subtitle2' fontWeight='500'>
                {filter.label}
              </Typography>
            </FormLabel>
            <FormControl variant='outlined' fullWidth size='small' sx={{ mt: 0.5 }}>
              {renderFilterInput(filter, filterValues, handleFilterChange)}
            </FormControl>
          </Grid>
        ))}
      </Grid>
    </Popover>
  );
};

export default FilterPopover;
