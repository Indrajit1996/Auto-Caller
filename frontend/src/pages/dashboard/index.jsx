import DashboardSevenScreen from './HomeSevenScreen';
import DashboardSingleScreen from './SingleScreen';

export const Dashboard = () => {
  const isSevenScreen = import.meta.env.VITE_SEVEN_SCREEN_DASHBOARD_LAYOUT_ENABLED === 'true';
  return isSevenScreen ? <DashboardSevenScreen /> : <DashboardSingleScreen />;
};
