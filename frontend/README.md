# Keystone Frontend

### Install packages

```
docker exec frontend-container pnpm add package-name
```

## Layouts

We utilize different layouts to manage the structure and presentation of various screens. The layouts include:

### 1. **Admin Layout**

The `AdminLayout` checks if the user is authenticated and whether they have superuser privileges. If the user is not authenticated, they are redirected to the login page. If the user lack superuser access, a forbidden error page is displayed.

### 2. **App Layout**

The `AppLayout` serves as the main layout for the application, providing a consistent header and main content area. It wraps the main application components and can include a sidebar for navigation. This layout is ideal for general application views that require a standard structure.

### 3. **Auth Layout**

The `AuthLayout` wraps auth-related pages, such as login and registration. It checks if the user is already authenticated; if so, they are redirected to the logged-in home page.

### 4. **Dashboard Layout**

The `DashboardLayout` accommodates both single-screen and seven-screen layouts. It checks the environment variable `VITE_SEVEN_SCREEN_DASHBOARD_LAYOUT_ENABLED` to determine which layout to render.

### 5. **Protected Layout**

The `ProtectedLayout` ensures only authenticated users can access certain routes.

### When to Use Each Layout

- **Use `AdminLayout`** for administrative interfaces requiring superuser access.
- **Use `AppLayout`** for general application views that need a consistent structure.
- **Use `AuthLayout`** for authentication-related pages to manage user login and registration flows.
- **Update the env variable `VITE_SEVEN_SCREEN_DASHBOARD_LAYOUT_ENABLED` to render a specific `DashboardLayout`**.
- **Use `ProtectedLayout`** to secure routes and ensure that only authenticated users can access specific areas of the application.
