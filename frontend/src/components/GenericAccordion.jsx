import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { Accordion, AccordionDetails, AccordionSummary, Typography } from '@mui/material';

const GenericAccordion = ({ id, title, expanded, onChange, children }) => {
  return (
    <Accordion
      expanded={expanded === id}
      onChange={onChange(id)}
      elevation={0}
      disableGutters
      sx={{
        mb: 2,
        border: '1px solid',
        borderColor: 'divider',
        '&:before': {
          display: 'none',
        },
        '&.Mui-expanded': {
          boxShadow: 'none',
        },
        borderRadius: '8px !important',
        overflow: 'hidden',
      }}
    >
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        sx={{
          backgroundColor: 'background.default',
          '&:hover': {
            backgroundColor: 'action.hover',
          },
        }}
      >
        <Typography
          sx={{
            fontWeight: 600,
            color: 'text.primary',
          }}
        >
          {title}
        </Typography>
      </AccordionSummary>
      <AccordionDetails sx={{ p: 3, backgroundColor: 'background.paper' }}>
        {children}
      </AccordionDetails>
    </Accordion>
  );
};

export default GenericAccordion;
