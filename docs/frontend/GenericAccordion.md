# GenericAccordion Component

A customized accordion component with consistent styling and enhanced user experience.

## Features

- Custom styling with border and rounded corners
- Hover effects
- Expandable/collapsible content
- Custom background colors

## Props

| Prop     | Type      | Description                   |
| -------- | --------- | ----------------------------- |
| id       | string    | Unique identifier             |
| title    | string    | Accordion header text         |
| expanded | string    | Current expanded accordion ID |
| onChange | function  | Handler for expand/collapse   |
| children | ReactNode | Accordion content             |

## Usage Example

```javascript
const [expanded, setExpanded] = useState(false);
const handleChange = (panel) => (event, isExpanded) => {
setExpanded(isExpanded ? panel : false);
};
<GenericAccordion
id="panel1"
title="Section 1"
expanded={expanded === 'panel1'}
onChange={handleChange}
>
<Typography>
This is the content of section 1
</Typography>
</GenericAccordion>
<GenericAccordion
id="panel2"
title="Section 2"
expanded={expanded === 'panel2'}
onChange={handleChange}
>
<Typography>
This is the content of section 2
</Typography>
</GenericAccordion>
```

## Notes

- Customizable content area
- Smooth expand/collapse transitions
