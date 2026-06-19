import React from 'react';
import {NavbarWrapper} from '../navbar/navbar';

interface Props {
   children: React.ReactNode;
}

export const Layout = ({children}: Props) => {
   return <NavbarWrapper>{children}</NavbarWrapper>;
};
