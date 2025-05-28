import ChipsFilter from './Filters/ChipsFilter';
import DateRangeFilter from './Filters/DateRangeFilter';
import MultiSelectFilter from './Filters/MultiSelectFilter';
import RangeFilter from './Filters/RangeFilter';
import SelectFilter from './Filters/SelectFilter';
import TextFilter from './Filters/TextFilter';

// Component map for filter types
const FILTER_COMPONENTS = {
  multi: MultiSelectFilter,
  range: RangeFilter,
  date: DateRangeFilter,
  text: TextFilter,
  select: SelectFilter,
  chips: ChipsFilter,
};

export const renderFilterInput = (filter, filterValues, handleFilterChange) => {
  // Default to 'select' if no type is specified
  const filterType = filter.type || (filter.multi ? 'multi' : 'select');

  // Get the component from the map, fallback to SelectFilter
  const FilterComponent = FILTER_COMPONENTS[filterType] || FILTER_COMPONENTS.select;

  // Render the component with props
  return (
    <FilterComponent
      filter={filter}
      filterValues={filterValues}
      handleFilterChange={handleFilterChange}
    />
  );
};

export const clearFilter = (key, handleFilterChange) => {
  handleFilterChange(key, '__clear__');
};
