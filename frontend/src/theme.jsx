import '@fontsource/roboto';
import { createTheme } from '@mui/material';

const fontFamily = 'Roboto';

const neutral = {
  50: '#fafafa',
  100: '#f5f5f5',
  200: '#eeeeee',
  300: '#e0e0e0',
  400: '#bdbdbd',
  500: '#9e9e9e',
  600: '#757575',
  700: '#616161',
  800: '#424242',
  900: '#212121',
  A100: '#f5f5f5',
  A200: '#eeeeee',
  A400: '#bdbdbd',
  A700: '#616161',
};

const theme = createTheme({
  palette: {
    neutral: {
      ...neutral,
      main: neutral[700],
      contrastText: '#fff',
      dark: neutral[800],
      light: neutral[500],
    },
  },
  typography: {
    fontFamily: [
      fontFamily, // Primary font
      '-apple-system', // Fallback fonts
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        // This affects all HTML elements
        '*': {
          fontFamily: [
            fontFamily,
            '-apple-system',
            'BlinkMacSystemFont',
            '"Segoe UI"',
            'Roboto',
            '"Helvetica Neue"',
            'Arial',
            'sans-serif',
          ].join(','),
        },
      },
    },
  },
});

export default theme;
