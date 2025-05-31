// App.tsx
import React, { useState, Suspense } from 'react';
import { ReactKeycloakProvider } from '@react-keycloak/web';
import Keycloak, { KeycloakInstance } from 'keycloak-js';
import ReportPage from './components/ReportPage';

// Расширяем интерфейс KeycloakInitOptions для поддержки дополнительных параметров
declare module 'keycloak-js' {
  interface KeycloakInitOptions {
    extraQueryParams?: Record<string, any>; // Позволяет добавлять произвольные параметры
  }
}

// Конфигурация Keycloak
const keycloakConfig: Keycloak.KeycloakConfig = {
  url: process.env.REACT_APP_KEYCLOAK_URL || '',
  realm: process.env.REACT_APP_KEYCLOAK_REALM || '',
  clientId: process.env.REACT_APP_KEYCLOAK_CLIENT_ID || ''
};

// Генерация случайного code verifier
function generateCodeVerifier(): string {
  let array = new Uint8Array(32);
  window.crypto.getRandomValues(array);
  return btoa(
    String.fromCharCode(...Array.from(array))
  )
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');
}

// Генерация challenge из code verifier
async function createCodeChallenge(codeVerifier: string): Promise<string> {
  const hashBuffer = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(codeVerifier));
  return btoa(
    String.fromCharCode(...Array.from(new Uint8Array(hashBuffer)))
  )
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');
}

// Основной компонент приложения
const App: React.FC = () => {
  const [keycloakInstance, setKeycloakInstance] = useState<KeycloakInstance | null>(null);

  async function initializeKeycloak() {
    try {
      const codeVerifier = generateCodeVerifier();
      const codeChallenge = await createCodeChallenge(codeVerifier);

      const keycloak = new Keycloak(keycloakConfig);

      // Определяем параметры авторизации вручную
      localStorage.setItem('pkce_code_verifier', codeVerifier); // Сохраняем code verifier локально

      await keycloak.init({
        onLoad: 'login-required',
        checkLoginIframe: false,
        pkceMethod: 'S256', // Метод шифрования для PKCE
        extraQueryParams: {
          code_challenge: codeChallenge,
          code_challenge_method: 'S256'
        }
      });

      setKeycloakInstance(keycloak);
    } catch (err) {
      console.error("Error initializing Keycloak:", err);
    }
  };

  if (!keycloakInstance) {
    initializeKeycloak();
    return <div>Initializing...</div>;
  }

  return (
    <Suspense fallback={<div>Loading...</div>}>
      <ReactKeycloakProvider authClient={keycloakInstance}>
        <div className="App">
          <ReportPage />
        </div>
      </ReactKeycloakProvider>
    </Suspense>
  );
};

export default App;