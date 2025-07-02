// index.jsx
import { createRoot } from 'react-dom/client';

import { App } from './App.jsx';

const container = document.getElementById('root');
const root = createRoot(container);

// Add cleanup for development mode
if (import.meta.env.DEV) {
  if (import.meta.hot) {
    import.meta.hot.dispose(() => {
      root.unmount();
    });
  }
}

root.render(<App />);
