import { useNavigate } from 'react-router';
import { useAuth } from '@/hooks';
import Login from './loginPage/Login';

export const LandingPage = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  return <Login />;
};
