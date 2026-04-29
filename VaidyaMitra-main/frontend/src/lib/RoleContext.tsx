'use client';
import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';

type Role = 'doctor' | 'patient' | null;

interface RoleContextType {
    role: Role;
    setRole: (role: Role) => void;
}

const RoleContext = createContext<RoleContextType | undefined>(undefined);

export function RoleProvider({ children }: { children: ReactNode }) {
    const [role, setRoleState] = useState<Role>(null);
    const [isMounted, setIsMounted] = useState(false);

    useEffect(() => {
        setIsMounted(true);
        const storedRole = localStorage.getItem('vaidyamitra-role') as Role;
        if (storedRole === 'doctor' || storedRole === 'patient') {
            setRoleState(storedRole);
        }
    }, []);

    const setRole = (newRole: Role) => {
        setRoleState(newRole);
        if (newRole) {
            localStorage.setItem('vaidyamitra-role', newRole);
        } else {
            localStorage.removeItem('vaidyamitra-role');
        }
    };

    // Return null while checking local storage on first mount to prevent hydration mismatch with the welcome screen
    if (!isMounted) return null;

    return (
        <RoleContext.Provider value={{ role, setRole }}>
            {children}
        </RoleContext.Provider>
    );
}

export function useRole() {
    const context = useContext(RoleContext);
    if (context === undefined) {
        throw new Error('useRole must be used within a RoleProvider');
    }
    return context;
}
