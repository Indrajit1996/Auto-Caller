import { Checkbox, FormControlLabel, FormGroup } from '@mui/material';

const MultiSelectFilter = ({ filter, filterValues, handleFilterChange }) => {
  const selectedValues = Array.isArray(filterValues[filter.id]) ? filterValues[filter.id] : [];

  const handleToggle = (value) => {
    // If "All" is selected, clear the selection
    if (value === '') {
      handleFilterChange(filter.id, []);
      return;
    }

    // Check if value is already selected
    const isSelected = selectedValues.includes(value);
    let newValues;

    if (isSelected) {
      // Remove the value if already selected
      newValues = selectedValues.filter((val) => val !== value);
    } else {
      // Add the value if not selected
      newValues = [...selectedValues, value];
    }

    handleFilterChange(filter.id, newValues);
  };

  // All is checked when no values are selected
  const isAllSelected = selectedValues.length === 0;

  return (
    <FormGroup style={{ paddingLeft: '8px' }}>
      <FormControlLabel
        control={
          <Checkbox
            checked={isAllSelected}
            onChange={() => handleToggle('')}
            size='small'
            color='primary'
          />
        }
        label='All'
      />
      {filter.options.map((option) => {
        const isSelected = selectedValues.includes(option.value);

        return (
          <FormControlLabel
            key={option.value}
            control={
              <Checkbox
                checked={isSelected}
                onChange={() => handleToggle(option.value)}
                size='small'
                color='primary'
              />
            }
            label={option.label}
          />
        );
      })}
    </FormGroup>
  );
};

export default MultiSelectFilter;
