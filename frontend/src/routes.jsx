import { Routes } from 'react-router';
import { Route } from 'react-router';
import { BrowserRouter } from 'react-router';

import ErrorPage from '@/components/Error/ErrorPage';
import { ROUTES } from '@/constants/routeConstants';
import { AdminLayout } from '@/layouts/AdminLayout';
import { AuthLayout } from '@/layouts/AuthLayout';
import { DashboardLayout } from '@/layouts/DashboardLayout';
import { AppLayout } from '@/layouts/base/AppLayout';
import { ProtectedLayout } from '@/layouts/base/ProtectedLayout';
import { GroupDetail, Groups, Invites, Profile, UserDetail, Users } from '@/pages/admin';
import Login from '@/pages/loginPage/Login';
import Register from '@/pages/loginPage/Register';
import ResetPassword from '@/pages/loginPage/ResetPassword';
import VerifyEmail from '@/pages/loginPage/VerifyRegistration';
import ForgotPassword from '@/pages/loginPage/ForgotPassword';
import { Dashboard } from '@/pages/dashboard';
import ConversationPage from '@/pages/conversation';

export const Router = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AuthLayout />}>
          <Route path={ROUTES.LANDING_PAGE} element={<Login />} />
          <Route path={ROUTES.AUTH.LOGIN} element={<Login />} />
          <Route path={ROUTES.AUTH.REGISTER} element={<Register />} />
          <Route path={ROUTES.AUTH.RESET_PASSWORD} element={<ResetPassword />} />
          <Route path={ROUTES.AUTH.VERIFY_EMAIL} element={<VerifyEmail />} />
          <Route path={ROUTES.AUTH.FORGOT_PASSWORD} element={<ForgotPassword />} />
        </Route>

        <Route element={<DashboardLayout />}>
          <Route path={ROUTES.LOGGED_IN_HOME} element={<Dashboard />} />
          <Route path={ROUTES.CONVERSATION} element={<ConversationPage />} />
        </Route>

        <Route element={<AdminLayout />}>
          <Route path={ROUTES.ADMIN.USERS} element={<Users />} />
          <Route path={ROUTES.ADMIN.USERS_DETAIL} element={<UserDetail />} />
          <Route path={ROUTES.ADMIN.INVITES} element={<Invites />} />
          <Route path={ROUTES.ADMIN.GROUPS} element={<Groups />} />
          <Route path={ROUTES.ADMIN.GROUP_DETAIL} element={<GroupDetail />} />
        </Route>

        <Route
          path={ROUTES.PROFILE}
          element={
            <ProtectedLayout>
              <AppLayout>
                <Profile />
              </AppLayout>
            </ProtectedLayout>
          }
        />
        <Route path='*' element={<ErrorPage code='404' />} />
      </Routes>
    </BrowserRouter>
  );
};
