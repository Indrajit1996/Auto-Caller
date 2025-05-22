import { ListItemText, MenuItem, Select } from '@mui/material';

const SelectFilter = ({ filter, filterValues, handleFilterChange }) => {
  // Get the current value or empty string if not set
  const currentValue = filterValues[filter.id] !== undefined ? filterValues[filter.id] : '';

  // Check if the selected option exists
  const selectedOption =
    currentValue !== '' ? filter.options.find((o) => o.value === currentValue) : null;

  // Determine what to display
  const displayValue =
    currentValue === '' ? 'All' : selectedOption ? selectedOption.label : currentValue;

  // add all option to filters if not exists
  const options = filter.options;
  if (!options.find((option) => ['', null, 'all'].includes(option.value))) {
    options.unshift({ label: 'All', value: '' });
  }

  return (
    <Select
      fullWidth
      variant='outlined'
      id={`filter-${filter.id}`}
      value={currentValue}
      displayEmpty
      onChange={(e) => handleFilterChange(filter.id, e.target.value)}
      renderValue={() => displayValue}
    >
      {filter.options.map((option) => (
        <MenuItem key={option.value} value={option.value}>
          <ListItemText primary={option.label} />
        </MenuItem>
      ))}
    </Select>
  );
};

export default SelectFilter;
