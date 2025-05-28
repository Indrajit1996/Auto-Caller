import Box from '@mui/material/Box';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';

import { clearFilter } from '../utils';

const DateRangeFilter = ({ filter, filterValues, handleFilterChange }) => {
  const dateValue = filterValues[filter.id] || [null, null];

  const handleStartDateChange = (date) => {
    if (date && date.isValid && date.isValid()) {
      handleFilterChange(filter.id, [date, dateValue[1]]);
    } else if (!date && !dateValue[1]) {
      clearFilter(filter.id, handleFilterChange);
    } else if (!date) {
      handleFilterChange(filter.id, [null, dateValue[1]]);
    }
  };

  const handleEndDateChange = (date) => {
    if (date && date.isValid && date.isValid()) {
      handleFilterChange(filter.id, [dateValue[0], date]);
    } else if (!date && !dateValue[0]) {
      clearFilter(filter.id, handleFilterChange);
    } else if (!date) {
      handleFilterChange(filter.id, [dateValue[0], null]);
    }
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <Box display='flex' flexDirection='column' gap={2}>
        <DatePicker
          autoOk
          variant='inline'
          inputVariant='outlined'
          label='From'
          disableFuture
          value={dateValue[0]}
          onChange={handleStartDateChange}
          maxDate={dateValue[1] || undefined}
          KeyboardButtonProps={{
            'aria-label': 'change start date',
          }}
          size='small'
          fullWidth
          InputProps={{
            style: {
              paddingRight: 0,
            },
          }}
        />

        <DatePicker
          autoOk
          variant='inline'
          inputVariant='outlined'
          label='To'
          value={dateValue[1]}
          onChange={handleEndDateChange}
          minDate={dateValue[0] || undefined}
          KeyboardButtonProps={{
            'aria-label': 'change end date',
          }}
          size='small'
          fullWidth
          InputProps={{
            style: {
              paddingRight: 0,
            },
          }}
        />
      </Box>
    </LocalizationProvider>
  );
};

export default DateRangeFilter;
