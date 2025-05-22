import { Box, Chip } from '@mui/material';

const ChipFilter = ({ filter, filterValues, handleFilterChange }) => {
  const selectedValue = filterValues[filter.id] || filter.defaultValue || '';

  return (
    <Box display='flex' flexWrap='wrap' gap={1} mb={1}>
      {filter.options.map((option) => (
        <Chip
          key={option.value}
          label={option.label}
          onClick={() => handleFilterChange(filter.id, option.value)}
          color={selectedValue === option.value ? 'primary' : 'default'}
          variant={selectedValue === option.value ? 'default' : 'outlined'}
          clickable
        />
      ))}
    </Box>
  );
};

const ChipsFilters = ({ filters, filterValues, handleFilterChange }) => {
  // Only get chip filters
  const chipFilters = filters.filter((filter) => filter.type === 'chips');

  if (chipFilters.length === 0) {
    return null;
  }

  // add All option to filters
  chipFilters.forEach((filter) => {
    if (!filter.options.find((option) => ['', null, 'all'].includes(option.value))) {
      filter.options.unshift({ label: 'All', value: '' });
    }
  });

  return (
    <Box mb={4}>
      {chipFilters.map((filter) => (
        <ChipFilter
          key={filter.id}
          filter={filter}
          filterValues={filterValues}
          handleFilterChange={handleFilterChange}
        />
      ))}
    </Box>
  );
};

export default ChipsFilters;
