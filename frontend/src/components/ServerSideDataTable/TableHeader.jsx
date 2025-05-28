import {
  FilterList,
  Search as SearchIcon,
  ViewColumn as ViewColumnIcon,
} from '@mui/icons-material';
import CloseIcon from '@mui/icons-material/Close';
import {
  Box,
  Button,
  Chip,
  IconButton,
  InputAdornment,
  TextField,
  Typography,
} from '@mui/material';

const TableHeader = ({
  search,
  setSearch,
  filters,
  activeFilterCount,
  handleFilterToggle,
  clearFilters,
  hiddenColumnsCount,
  handleColumnMenuOpen,
  children,
}) => {
  return (
    <Box display='flex' justifyContent='space-between' alignItems='center' mb={2} gap={2}>
      <Box display='flex' gap={2} alignItems='center'>
        <TextField
          size='small'
          variant='outlined'
          label='Search'
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder='Start typing to search...'
          slotProps={{
            input: {
              endAdornment: (
                <InputAdornment position='end'>
                  {search ? (
                    <IconButton onClick={() => setSearch('')} edge='end' size='small'>
                      <CloseIcon />
                    </IconButton>
                  ) : (
                    <SearchIcon color='action' />
                  )}
                </InputAdornment>
              ),
            },
          }}
        />
        {filters.length > 0 && (
          <>
            <Button
              variant='outlined'
              color={activeFilterCount > 0 ? 'primary' : 'neutral'}
              startIcon={<FilterList />}
              endIcon={
                activeFilterCount > 0 && (
                  <Chip
                    size='small'
                    label={<Typography variant='body2'>{activeFilterCount}</Typography>}
                    color='primary'
                  />
                )
              }
              onClick={handleFilterToggle}
              aria-describedby='filter-popover'
            >
              Filters
            </Button>
            {activeFilterCount > 0 && (
              <Button
                onClick={clearFilters}
                variant='outlined'
                color='error'
                startIcon={<CloseIcon />}
                disabled={activeFilterCount === 0}
              >
                Clear Filters
              </Button>
            )}
          </>
        )}
      </Box>
      <Box display='flex' alignItems='center' gap={2}>
        <Button
          variant='outlined'
          color={hiddenColumnsCount > 0 ? 'primary' : 'neutral'}
          startIcon={<ViewColumnIcon />}
          endIcon={
            hiddenColumnsCount > 0 && (
              <Chip
                size='small'
                label={<Typography variant='body2'>{hiddenColumnsCount}</Typography>}
                color='primary'
              />
            )
          }
          onClick={handleColumnMenuOpen}
          aria-controls='column-menu'
          aria-haspopup='true'
        >
          Columns
        </Button>
        {children}
      </Box>
    </Box>
  );
};

export default TableHeader;
