import { useCallback, useEffect, useRef, useState } from 'react';

import { Paper, TableContainer } from '@mui/material';
import { useLocation, useNavigate } from 'react-router';

import useDebounce from '@/hooks/useDebounce';

import ChipsFilters from './ChipsFilters';
import ColumnVisibilityPopover from './ColumnVisibilityPopover';
import DataTable from './DataTable';
import FilterPopover from './FilterPopover';
import SelectedFilters from './SelectedFilters';
import TableHeader from './TableHeader';
import ToggleDisplayMode from './ToggleDisplayMode';

/**
 * ServerSideDataTable - A simplified data table with URL parameter state persistence
 */
const ServerSideDataTable = ({
  data,
  columns,
  totalCount,
  fetchData,
  defaultSort = { order: 'desc', orderBy: 'created_at' },
  defaultRowsPerPage = 10,
  loading = false,
  filters = [],
  defaultFilters = {},
  persistState = true,
  refreshDataTrigger = null,
  defaultDisplayMode = 'normal', // New prop for default display mode
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [filterAnchorEl, setFilterAnchorEl] = useState(null);
  const [columnMenuAnchorEl, setColumnMenuAnchorEl] = useState(null);

  // Prevent initial URL update on mount
  const isInitialMount = useRef(true);

  // Check if URL has parameters
  const hasUrlParams = useRef(false);

  // Parse URL parameters on mount
  const parseUrlParams = useCallback(() => {
    if (!persistState) return null;

    const searchParams = new URLSearchParams(location.search);

    // Check if there are any parameters in the URL
    hasUrlParams.current = searchParams.toString().length > 0;

    // Extract basic parameters
    const urlOrder = searchParams.get('order');
    const urlOrderBy = searchParams.get('orderBy');
    const urlPage = searchParams.get('page');
    const urlRowsPerPage = searchParams.get('rowsPerPage');
    const urlSearch = searchParams.get('search');
    const urlHiddenColumns = searchParams.get('hiddenColumns');

    // Extract display mode
    const urlDisplayMode = searchParams.get('displayMode');

    // Extract filter values
    const urlFilters = {};
    filters.forEach((filter) => {
      const filterValue = searchParams.get(`filter_${filter.id}`);
      if (filterValue !== null) {
        try {
          // Handle complex filter types that should be parsed from JSON
          if (['date', 'range', 'multi'].includes(filter.type)) {
            try {
              const parsedValue = JSON.parse(filterValue);
              urlFilters[filter.id] = parsedValue;
            } catch (e) {
              console.warn(`Failed to parse JSON for filter ${filter.id}, using as string:`, e);
              urlFilters[filter.id] = filterValue;
            }
          } else {
            // Default case: use as string
            urlFilters[filter.id] = filterValue;
          }
        } catch (error) {
          console.warn(`Error processing filter ${filter.id}:`, error);
          urlFilters[filter.id] = filterValue; // Fallback to raw value
        }
      }
    });

    // Parse hidden columns
    let parsedHiddenColumns = null;
    if (urlHiddenColumns) {
      try {
        parsedHiddenColumns = JSON.parse(urlHiddenColumns);
      } catch (e) {
        console.error('Error parsing hidden columns from URL', e);
      }
    }

    // Determine which filters to use:
    // - If URL has any parameters, only use the filters explicitly set in URL
    // - If URL is empty, fall back to defaultFilters
    const finalFilters = hasUrlParams.current ? urlFilters : defaultFilters;

    return {
      order: urlOrder || defaultSort.order,
      orderBy: urlOrderBy || defaultSort.orderBy,
      page: urlPage ? parseInt(urlPage, 10) : 0,
      rowsPerPage: urlRowsPerPage ? parseInt(urlRowsPerPage, 10) : defaultRowsPerPage,
      search: urlSearch || '',
      filterValues: finalFilters,
      hiddenColumns: parsedHiddenColumns,
      displayMode: urlDisplayMode || defaultDisplayMode, // Use defaultDisplayMode if not in URL
    };
  }, [
    location.search,
    persistState,
    defaultSort,
    defaultRowsPerPage,
    filters,
    defaultFilters,
    defaultDisplayMode,
  ]);

  // Initialize state from URL params or defaults
  const initialState = parseUrlParams();

  const [order, setOrder] = useState(initialState?.order || defaultSort.order);
  const [orderBy, setOrderBy] = useState(initialState?.orderBy || defaultSort.orderBy);
  const [page, setPage] = useState(initialState?.page || 0);
  const [rowsPerPage, setRowsPerPage] = useState(initialState?.rowsPerPage || defaultRowsPerPage);
  const [search, setSearch] = useState(initialState?.search || '');
  const [filterValues, setFilterValues] = useState(initialState?.filterValues || defaultFilters);

  // Initialize display mode with priority:
  // 1. URL parameter (if present)
  // 2. Default display mode prop
  const [isCompactMode, setIsCompactMode] = useState(() => {
    // If URL has displayMode parameter, use that
    if (initialState?.displayMode) {
      return initialState.displayMode === 'compact';
    }
    // Otherwise use the default from props
    return defaultDisplayMode === 'compact';
  });

  // Calculate default column visibility
  const getDefaultVisibility = useCallback(() => {
    return columns.reduce(
      (acc, column) => ({ ...acc, [column.id]: column?.hidden ? false : true }),
      {}
    );
  }, [columns]);

  // Get the default visibility state
  const defaultVisibility = getDefaultVisibility();

  // Initialize column visibility state
  const [visibleColumns, setVisibleColumns] = useState(() => {
    // If URL contains hiddenColumns parameter, prioritize it
    if (hasUrlParams.current && initialState?.hiddenColumns) {
      return { ...defaultVisibility, ...initialState.hiddenColumns };
    }

    // Otherwise use default visibility
    return defaultVisibility;
  });

  // Handle toggle display mode
  const handleToggleDisplayMode = useCallback((compact) => {
    setIsCompactMode(compact);
  }, []);

  // Derived state
  const filteredColumns = columns.filter((column) => visibleColumns[column.id]);
  const hiddenColumnsCount = columns.length - filteredColumns.length;
  const debouncedSearch = useDebounce(search, 500);
  const debouncedFilters = useDebounce(filterValues, 500);
  const isFilterOpen = Boolean(filterAnchorEl);
  const activeFilterCount = Object.values(filterValues).filter(
    (value) => value !== '' && value !== null && (Array.isArray(value) ? value.length > 0 : true)
  ).length;

  // Function to update URL with current state (simplified without prefixes)
  const updateUrlParams = useCallback(() => {
    if (!persistState) return;

    const currentPath = location.pathname;
    const searchParams = new URLSearchParams();

    // Set basic parameters
    searchParams.set('order', order);
    searchParams.set('orderBy', orderBy);
    searchParams.set('page', page.toString());
    searchParams.set('rowsPerPage', rowsPerPage.toString());

    // Only include search if it exists
    if (search) {
      searchParams.set('search', search);
    }

    // Include display mode
    searchParams.set('displayMode', isCompactMode ? 'compact' : 'normal');

    // Include hidden columns - only if different from default
    if (hiddenColumnsCount > 0 || columns.some((col) => col.hidden && visibleColumns[col.id])) {
      const hiddenColumnsObj = {};
      const defaultVis = getDefaultVisibility();

      // Include columns where visibility differs from default
      columns.forEach((column) => {
        // Always include visibility state if it differs from the default
        if (visibleColumns[column.id] !== defaultVis[column.id]) {
          hiddenColumnsObj[column.id] = visibleColumns[column.id];
        }
        // Special case: also include when a hidden column is made visible
        else if (column.hidden && visibleColumns[column.id]) {
          hiddenColumnsObj[column.id] = true;
        }
      });

      // Only add parameter if there are overrides
      if (Object.keys(hiddenColumnsObj).length > 0) {
        searchParams.set('hiddenColumns', JSON.stringify(hiddenColumnsObj));
      }
    }

    // Set filter values
    Object.entries(filterValues).forEach(([key, value]) => {
      if (value !== '' && value !== null) {
        if (Array.isArray(value)) {
          searchParams.set(`filter_${key}`, JSON.stringify(value));
        } else {
          searchParams.set(`filter_${key}`, value.toString());
        }
      }
    });

    // Update URL without triggering a navigation
    const newUrl = `${currentPath}?${searchParams.toString()}`;
    // Use replace to avoid adding to history
    navigate(newUrl, { replace: true });
  }, [
    persistState,
    navigate,
    order,
    orderBy,
    page,
    rowsPerPage,
    search,
    hiddenColumnsCount,
    columns,
    visibleColumns,
    filterValues,
    getDefaultVisibility,
    isCompactMode,
  ]);

  // Event handlers
  const handleFilterToggle = (event) => {
    setFilterAnchorEl(filterAnchorEl ? null : event.currentTarget);
  };

  const handleCloseFilters = () => {
    setFilterAnchorEl(null);
  };

  const handleColumnMenuOpen = (event) => {
    setColumnMenuAnchorEl(event.currentTarget);
  };

  const handleColumnMenuClose = () => {
    setColumnMenuAnchorEl(null);
  };

  const toggleColumnVisibility = (columnId) => {
    setVisibleColumns((prev) => ({
      ...prev,
      [columnId]: !prev[columnId],
    }));
  };

  const resetColumnVisibility = () => {
    // Reset to default column visibility
    setVisibleColumns(getDefaultVisibility());
  };

  const handleRequestSort = (event, property) => {
    const isAsc = orderBy === property && order === 'asc';
    const newOrder = isAsc ? 'desc' : 'asc';
    setOrder(newOrder);
    setOrderBy(property);
  };

  const handlePageChange = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    const newRowsPerPage = parseInt(event.target.value, 10);
    setRowsPerPage(newRowsPerPage);
    setPage(0);
  };

  const handleSearchChange = (newSearch) => {
    setSearch(newSearch);
    setPage(0); // Reset to first page on search change
  };

  const handleFilterChange = useCallback(
    (filterId, value) => {
      setFilterValues((prev) => {
        const filter = filters.find((f) => f.id === filterId);
        if (!filter) return prev;

        const filterType = filter.type;

        if (value === '__clear__') {
          const { [filterId]: _, ...rest } = prev;
          return rest;
        }

        let updatedFilters;
        switch (filterType) {
          case 'multi': {
            const currentValues = Array.isArray(prev[filterId]) ? [...prev[filterId]] : [];

            if (value === '' || (Array.isArray(value) && value.length === 0)) {
              updatedFilters = { ...prev, [filterId]: [] };
            } else if (Array.isArray(value)) {
              updatedFilters = { ...prev, [filterId]: value };
            } else {
              const valueIndex = currentValues.indexOf(value);
              if (valueIndex === -1) {
                updatedFilters = { ...prev, [filterId]: [...currentValues, value] };
              } else {
                currentValues.splice(valueIndex, 1);
                updatedFilters = { ...prev, [filterId]: currentValues.length ? currentValues : '' };
              }
            }
            break;
          }

          case 'date':
          case 'range':
            updatedFilters = { ...prev, [filterId]: Array.isArray(value) ? value : [] };
            break;

          case 'text':
          case 'select':
          default:
            updatedFilters = { ...prev, [filterId]: value };
            break;
        }

        return updatedFilters;
      });

      setPage(0); // Reset to first page when filter changes
    },
    [filters]
  );

  const clearFilters = useCallback(() => {
    setFilterValues({});
    setPage(0);
  }, []);

  // Update URL when state changes
  useEffect(() => {
    // Skip initial render to prevent double URL updates
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return;
    }

    // Add throttling to avoid frequent URL updates
    const timeoutId = setTimeout(() => {
      updateUrlParams();
    }, 300); // Small delay to batch URL changes

    return () => clearTimeout(timeoutId);
  }, [updateUrlParams, order, orderBy, page, rowsPerPage, debouncedSearch, debouncedFilters]);

  // Separate effect for column visibility changes (less frequent)
  useEffect(() => {
    if (!isInitialMount.current) {
      updateUrlParams();
    }
  }, [visibleColumns, updateUrlParams]);

  // Track last refresh trigger to prevent double fetches
  const lastRefreshTrigger = useRef(refreshDataTrigger);

  // Fetch data when relevant parameters change
  useEffect(() => {
    // Handle refresh trigger separately
    if (refreshDataTrigger !== lastRefreshTrigger.current) {
      lastRefreshTrigger.current = refreshDataTrigger;
      fetchData(page, rowsPerPage, orderBy, order, debouncedSearch, debouncedFilters);
      return;
    }

    fetchData(page, rowsPerPage, orderBy, order, debouncedSearch, debouncedFilters);
  }, [
    page,
    rowsPerPage,
    orderBy,
    order,
    debouncedSearch,
    debouncedFilters,
    fetchData,
    refreshDataTrigger,
  ]);

  useEffect(() => {
    if (!isInitialMount.current) {
      updateUrlParams();
    }
  }, [isCompactMode, updateUrlParams]);

  // Simple filter context for rendering
  const getFilterContext = useCallback(() => {
    return filterValues;
  }, [filterValues]);

  return (
    <>
      <ChipsFilters
        filters={filters}
        filterValues={filterValues}
        handleFilterChange={handleFilterChange}
      />

      <TableHeader
        search={search}
        setSearch={handleSearchChange}
        filters={filters}
        activeFilterCount={activeFilterCount}
        handleFilterToggle={handleFilterToggle}
        clearFilters={clearFilters}
        hiddenColumnsCount={hiddenColumnsCount}
        handleColumnMenuOpen={handleColumnMenuOpen}
      >
        <ToggleDisplayMode isCompact={isCompactMode} onToggle={handleToggleDisplayMode} />
      </TableHeader>

      <ColumnVisibilityPopover
        columnMenuAnchorEl={columnMenuAnchorEl}
        handleColumnMenuClose={handleColumnMenuClose}
        columns={columns}
        visibleColumns={visibleColumns}
        toggleColumnVisibility={toggleColumnVisibility}
        resetColumnVisibility={resetColumnVisibility}
        filteredColumns={filteredColumns}
      />

      <FilterPopover
        isFilterOpen={isFilterOpen}
        filterAnchorEl={filterAnchorEl}
        handleCloseFilters={handleCloseFilters}
        filters={filters}
        filterValues={filterValues}
        handleFilterChange={handleFilterChange}
      />

      <SelectedFilters
        filterValues={filterValues}
        filters={filters}
        handleFilterChange={handleFilterChange}
      />

      <TableContainer component={Paper} variant='outlined'>
        <DataTable
          loading={loading}
          data={data}
          filteredColumns={filteredColumns}
          order={order}
          orderBy={orderBy}
          handleRequestSort={handleRequestSort}
          page={page}
          rowsPerPage={rowsPerPage}
          totalCount={totalCount}
          handlePageChange={handlePageChange}
          handleChangeRowsPerPage={handleChangeRowsPerPage}
          getFilterContext={getFilterContext}
          compact={isCompactMode} // Pass compact mode to DataTable
        />
      </TableContainer>
    </>
  );
};

export default ServerSideDataTable;
