import { Grid2 as Grid, Typography } from '@mui/material';

const DashboardSingleScreen = () => {
  return (
    <Grid
      container
      display='flex'
      justifyContent='center'
      alignItems='center'
      sx={{ height: '87vh' }}
    >
      <Typography variant='h4'>Single Screen</Typography>
    </Grid>
  );
};

export default DashboardSingleScreen;
