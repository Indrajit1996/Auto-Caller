import { Button, Grid2 as Grid, Stack, Typography } from '@mui/material';

export const PageHeader = ({
  title,
  subtitle,
  actions = [], // Array of action objects
}) => {
  return (
    <Grid container justifyContent='space-between' alignItems='center' sx={{ mb: 4 }}>
      <Grid>
        <Typography variant='h4' fontWeight={600}>
          {title}
        </Typography>
        {subtitle && (
          <Typography variant='body1' color='text.secondary'>
            {subtitle}
          </Typography>
        )}
      </Grid>
      {actions.length > 0 && (
        <Grid>
          <Stack direction='row' spacing={2}>
            {actions.map((action, index) => (
              <Button
                key={index}
                variant={action.variant || 'outlined'}
                onClick={action.onClick}
                startIcon={action.icon && <action.icon />}
                disabled={action.disabled}
                color={action.color || 'primary'}
              >
                {action.label}
              </Button>
            ))}
          </Stack>
        </Grid>
      )}
    </Grid>
  );
};
