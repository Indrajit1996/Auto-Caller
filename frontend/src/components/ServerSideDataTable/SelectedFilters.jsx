import { Box, Chip } from '@mui/material';

import { clearFilter } from './utils';

const renderFilterChip = (key, value, filters, handleFilterChange) => {
  const filter = filters.find((f) => f.id === key);
  if (
    !filter ||
    !value ||
    (Array.isArray(value) && value.length === 0) ||
    (Array.isArray(value) && value.every((item) => item === null || item === undefined))
  )
    return null;

  const filterType = filter.type || (filter.multi ? 'multi' : 'select');
  let chipLabel = filter.label;
  let filterLabel = filter.label;

  switch (filterType) {
    case 'range':
      // if either value is null, it means it's an open range, show like >= min or <= max
      if (value[0] === null) {
        chipLabel = `${filterLabel} ≤ ${value[1]}`;
      }
      if (value[1] === null) {
        chipLabel = `${filterLabel} ≥ ${value[0]}`;
      }
      if (value[0] !== null && value[1] !== null) {
        chipLabel = `${filterLabel}: ${value[0]} - ${value[1]}`;
      }
      break;
    case 'date':
      chipLabel = `${filterLabel}: ${value[0] ? (value[0].format ? value[0].format('MM/DD/YYYY') : value[0]) : 'Any'} - ${
        value[1] ? (value[1].format ? value[1].format('MM/DD/YYYY') : value[1]) : 'Any'
      }`;
      break;
    case 'text':
      chipLabel = `${filterLabel}: "${value}"`;
      break;
    case 'multi':
      if (Array.isArray(value)) {
        const selectedLabels = value.map((v) => {
          const option = filter.options.find((o) => o.value === v);
          return option ? option.label : v;
        });
        chipLabel = `${filterLabel}: ${selectedLabels.join(', ')}`;
      }
      break;
    case 'select':
    default: {
      const option = filter.options?.find((o) => o.value === value);
      chipLabel = option ? `${filterLabel}: ${option.label}` : `${filterLabel}: ${value}`;
      break;
    }
  }

  return (
    <Chip
      key={key}
      label={chipLabel}
      onDelete={() => clearFilter(key, handleFilterChange)}
      color='primary'
      variant='outlined'
    />
  );
};

const SelectedFilters = ({ filterValues, filters, handleFilterChange }) => {
  const activeFiltersWithoutChips = Object.entries(filterValues).filter(([key, value]) => {
    const filter = filters.find((f) => f.id === key);
    return filter && filter.type !== 'chips' && value;
  });

  if (activeFiltersWithoutChips.length === 0) return null;

  return (
    <Box display='flex' flexWrap='wrap' gap={1} mb={2}>
      {activeFiltersWithoutChips.map(([key, value]) =>
        renderFilterChip(key, value, filters, handleFilterChange)
      )}
    </Box>
  );
};

export default SelectedFilters;
