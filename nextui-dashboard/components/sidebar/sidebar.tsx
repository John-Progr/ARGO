import React from 'react';
import {Box} from '../styles/box';
import {Sidebar} from './sidebar.styles';
import {Flex} from '../styles/flex';
import {HomeIcon} from '../icons/sidebar/home-icon';
import {SidebarItem} from './sidebar-item';
import {useSidebarContext} from '../layout/layout-context';
import {useRouter} from 'next/router';

// Mathematical ARG logo — hexagon frame + normal-distribution bell curve
const ArgLogo = () => (
   <svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Hexagon */}
      <path
         d="M18 3 L31.5 10.5 L31.5 25.5 L18 33 L4.5 25.5 L4.5 10.5 Z"
         stroke="#0072F5"
         strokeWidth="1.8"
         fill="none"
      />
      {/* Bell curve (normal distribution) */}
      <path
         d="M9 23 C10.5 23 11.5 20 12.5 18 C13.5 16 14.5 13 18 13 C21.5 13 22.5 16 23.5 18 C24.5 20 25.5 23 27 23"
         stroke="#0072F5"
         strokeWidth="1.6"
         fill="none"
         strokeLinecap="round"
      />
      {/* Baseline */}
      <line x1="9" y1="23" x2="27" y2="23" stroke="#0072F5" strokeWidth="1" strokeOpacity="0.4" strokeLinecap="round"/>
      {/* Centre axis tick */}
      <line x1="18" y1="23" x2="18" y2="25" stroke="#0072F5" strokeWidth="1" strokeOpacity="0.6" strokeLinecap="round"/>
   </svg>
);

export const SidebarWrapper = () => {
   const router = useRouter();
   const {collapsed, setCollapsed} = useSidebarContext();

   return (
      <Box
         as="aside"
         css={{
            height: '100vh',
            zIndex: 202,
            position: 'sticky',
            top: '0',
         }}
      >
         {collapsed ? <Sidebar.Overlay onClick={setCollapsed} /> : null}

         <Sidebar collapsed={collapsed}>
            {/* ARG Branding */}
            <Sidebar.Header>
               <Flex align="center" css={{gap: '$3', px: '$2', py: '$2'}}>
                  <ArgLogo />
                  <Box>
                     <Box css={{fontWeight: '$bold', fontSize: '$lg', color: '$accents9', lineHeight: 1.15, letterSpacing: '-0.01em'}}>
                        ARG
                     </Box>
                     <Box css={{fontSize: '$xs', color: '$accents5', lineHeight: 1.2, letterSpacing: '0.04em'}}>
                        Risk Guardian
                     </Box>
                  </Box>
               </Flex>
            </Sidebar.Header>

            <Flex direction="column" justify="between" css={{height: '100%'}}>
               <Sidebar.Body className="body sidebar">
                  <SidebarItem
                     title="Dashboard"
                     icon={<HomeIcon />}
                     isActive={router.pathname === '/'}
                     href="/"
                  />
               </Sidebar.Body>
            </Flex>
         </Sidebar>
      </Box>
   );
};
