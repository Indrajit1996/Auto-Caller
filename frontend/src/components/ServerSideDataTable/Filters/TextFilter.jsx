import CloseIcon from '@mui/icons-material/Close';
import { IconButton, InputAdornment, TextField } from '@mui/material';

const TextFilter = ({ filter, filterValues, handleFilterChange }) => {
  const filterValue = filterValues[filter.id] || '';
  const hasValue = filterValue !== '';

  return (
    <TextField
      fullWidth
      variant='outlined'
      size='small'
      placeholder={filter.placeholder || 'Type to filter...'}
      value={filterValue}
      onChange={(e) => handleFilterChange(filter.id, e.target.value)}
      InputProps={{
        endAdornment: hasValue ? (
          <InputAdornment position='end'>
            <IconButton
              aria-label='clear filter'
              onClick={() => handleFilterChange(filter.id, '')}
              edge='end'
              size='small'
            >
              <CloseIcon fontSize='small' />
            </IconButton>
          </InputAdornment>
        ) : null,
      }}
    />
  );
};

export default TextFilter;
