import { Box, TextField, Typography } from '@mui/material';

const RangeFilter = ({ filter, filterValues, handleFilterChange }) => {
  // Default to null values instead of using min/max
  const rangeValue = filterValues[filter.id] || [null, null];

  // Convert string to number or null
  const parseNumericValue = (value) => {
    // Return null for empty string or invalid numbers
    if (value === '' || value === null || isNaN(Number(value))) return null;
    return Number(value);
  };

  const handleMinChange = (e) => {
    const newValue = parseNumericValue(e.target.value);
    const currentMax = rangeValue[1];

    // Only validate if both values are non-null
    if (newValue !== null && currentMax !== null) {
      // If min > max, set max equal to min
      if (newValue > currentMax) {
        handleFilterChange(filter.id, [newValue, newValue]);
      } else {
        handleFilterChange(filter.id, [newValue, currentMax]);
      }
    } else {
      // If either value is null, just update without validation
      handleFilterChange(filter.id, [newValue, currentMax]);
    }
  };

  const handleMaxChange = (e) => {
    const newValue = parseNumericValue(e.target.value);
    const currentMin = rangeValue[0];

    // Only validate if both values are non-null
    if (newValue !== null && currentMin !== null) {
      // If max < min, set min equal to max
      if (newValue < currentMin) {
        handleFilterChange(filter.id, [newValue, newValue]);
      } else {
        handleFilterChange(filter.id, [currentMin, newValue]);
      }
    } else {
      // If either value is null, just update without validation
      handleFilterChange(filter.id, [currentMin, newValue]);
    }
  };

  return (
    <Box display='flex' flexDirection='row' alignItems='center' gap={2}>
      <TextField
        variant='outlined'
        size='small'
        type='number'
        label='Min'
        value={rangeValue[0] === null ? '' : rangeValue[0]}
        onChange={(e) => handleMinChange(e)}
        inputProps={{
          min: filter.min,
          max: filter.max,
          step: filter.step || 1,
        }}
        style={{ width: '45%' }}
      />
      <Typography variant='body2' color='textSecondary'>
        to
      </Typography>
      <TextField
        variant='outlined'
        size='small'
        type='number'
        label='Max'
        value={rangeValue[1] === null ? '' : rangeValue[1]}
        onChange={(e) => handleMaxChange(e)}
        inputProps={{
          min: filter.min,
          max: filter.max,
          step: filter.step || 1,
        }}
        style={{ width: '45%' }}
      />
    </Box>
  );
};

export default RangeFilter;
