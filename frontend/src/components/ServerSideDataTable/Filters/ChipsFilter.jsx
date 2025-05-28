import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';

const ChipsFilter = ({ filter, filterValues, handleFilterChange }) => {
  const selectedValue = filterValues[filter.id] || 'All';

  return (
    <Box>
      <Chip
        label={filter.options.find((option) => option.value === selectedValue)?.label || 'All'}
        onDelete={() => handleFilterChange(filter.id, '')}
        clickable
        variant='outlined'
        color={selectedValue === 'All' ? 'default' : 'primary'}
      />
    </Box>
  );
};

export default ChipsFilter;
