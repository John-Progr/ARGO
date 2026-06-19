import {Navbar} from '@nextui-org/react';
import React from 'react';
import {Box} from '../styles/box';
import {DarkModeSwitch} from './darkmodeswitch';

interface Props {
   children: React.ReactNode;
}

// Argo ship + blockchain sail logo
// The mythological ship with a Web3 node-network for a sail
const ArgoLogo = () => (
   <svg width="38" height="34" viewBox="0 0 38 34" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Ship hull */}
      <path
         d="M2 21 Q19 29 36 21 L34 18 Q19 25 4 18 Z"
         fill="url(#hullGrad)"
      />
      {/* Keel / bow tip */}
      <path d="M34 18 Q37 17 36 21" fill="#0072F5" opacity="0.6"/>
      {/* Mast */}
      <line x1="19" y1="18" x2="19" y2="4" stroke="#00B4D8" strokeWidth="1.6" strokeLinecap="round"/>
      {/* Blockchain sail — nodes */}
      <circle cx="19" cy="4"  r="2.2" fill="#00D2FF"/>
      <circle cx="11" cy="10" r="1.7" fill="#00D2FF" opacity="0.9"/>
      <circle cx="27" cy="10" r="1.7" fill="#00D2FF" opacity="0.9"/>
      <circle cx="15" cy="15" r="1.5" fill="#00D2FF" opacity="0.8"/>
      <circle cx="23" cy="15" r="1.5" fill="#00D2FF" opacity="0.8"/>
      {/* Chain links (blockchain connections) */}
      <line x1="19" y1="4"  x2="11" y2="10" stroke="#00D2FF" strokeWidth="1.1" opacity="0.75"/>
      <line x1="19" y1="4"  x2="27" y2="10" stroke="#00D2FF" strokeWidth="1.1" opacity="0.75"/>
      <line x1="11" y1="10" x2="15" y2="15" stroke="#00D2FF" strokeWidth="1.1" opacity="0.65"/>
      <line x1="27" y1="10" x2="23" y2="15" stroke="#00D2FF" strokeWidth="1.1" opacity="0.65"/>
      <line x1="11" y1="10" x2="27" y2="10" stroke="#00D2FF" strokeWidth="0.8" opacity="0.4"/>
      <line x1="15" y1="15" x2="23" y2="15" stroke="#00D2FF" strokeWidth="0.8" opacity="0.4"/>
      {/* Wave */}
      <path
         d="M0 25 Q9.5 23 19 25 Q28.5 27 38 25"
         stroke="#0072F5" strokeWidth="1.3" fill="none" opacity="0.35" strokeLinecap="round"
      />
      <defs>
         <linearGradient id="hullGrad" x1="2" y1="18" x2="36" y2="18" gradientUnits="userSpaceOnUse">
            <stop offset="0%"   stopColor="#0050B3"/>
            <stop offset="50%"  stopColor="#0072F5"/>
            <stop offset="100%" stopColor="#0050B3"/>
         </linearGradient>
      </defs>
   </svg>
);

export const NavbarWrapper = ({children}: Props) => {
   return (
      <Box
         css={{
            position: 'relative',
            display: 'flex',
            flexDirection: 'column',
            flex: '1 1 auto',
            overflowY: 'auto',
            overflowX: 'hidden',
         }}
      >
         <Navbar
            {...({'isBordered': true} as any)}
            css={{
               'borderBottom': '1px solid $border',
               'width': '100%',
               '& .nextui-navbar-container': {
                  'border': 'none',
                  'maxWidth': '100%',
                  'px': '$8',
                  'justifyContent': 'space-between',
               },
            }}
         >
            {/* ARGO brand — left */}
            <Navbar.Content>
               <div style={{display: 'flex', alignItems: 'center', gap: '12px'}}>
                  <ArgoLogo />
                  <div style={{display: 'flex', flexDirection: 'column', lineHeight: 1}}>
                     <span
                        className="font-argo"
                        style={{
                           fontSize: '22px',
                           fontWeight: 700,
                           letterSpacing: '0.12em',
                           background: 'linear-gradient(90deg, #0072F5 0%, #00D2FF 100%)',
                           WebkitBackgroundClip: 'text',
                           WebkitTextFillColor: 'transparent',
                           backgroundClip: 'text',
                        }}
                     >
                        ARGO
                     </span>
                     <span
                        style={{
                           fontSize: '9px',
                           letterSpacing: '0.18em',
                           color: 'var(--nextui-colors-accents5)',
                           textTransform: 'uppercase',
                           marginTop: '1px',
                           fontFamily: "'Space Grotesk', sans-serif",
                        }}
                     >
                        Autonomous Risk Guardian Operator
                     </span>
                  </div>
               </div>
            </Navbar.Content>

            {/* Theme toggle — right */}
            <Navbar.Content>
               <DarkModeSwitch />
            </Navbar.Content>
         </Navbar>

         {children}
      </Box>
   );
};
