import '../styles/globals.css';
import type {AppProps} from 'next/app';
import {createTheme, NextUIProvider} from '@nextui-org/react';
import {ThemeProvider as NextThemesProvider, useTheme as useNextTheme} from 'next-themes';
import {Layout} from '../components/layout/layout';
import {useEffect} from 'react';

const lightTheme = createTheme({ type: 'light', theme: { colors: {} } });
const darkTheme  = createTheme({ type: 'dark',  theme: { colors: {} } });

// Bridges next-themes → Tailwind: keeps the `dark` class on <html> in sync
// so that all `dark:` Tailwind utilities activate correctly.
function ThemeSyncer() {
   const {resolvedTheme} = useNextTheme();
   useEffect(() => {
      document.documentElement.classList.toggle('dark', resolvedTheme === 'dark');
   }, [resolvedTheme]);
   return null;
}

function MyApp({Component, pageProps}: AppProps) {
   return (
      <NextThemesProvider
         defaultTheme="dark"
         attribute="class"
         value={{
            light: lightTheme.className,
            dark: darkTheme.className,
         }}
      >
         <ThemeSyncer />
         <NextUIProvider>
            <Layout>
               <Component {...pageProps} />
            </Layout>
         </NextUIProvider>
      </NextThemesProvider>
   );
}

export default MyApp;
