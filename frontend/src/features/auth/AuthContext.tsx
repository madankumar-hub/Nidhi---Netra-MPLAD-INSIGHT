import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { authApi } from '@/api'
import { tokenStore } from '@/api/client'
import type { TokenResponse, User, UserRole } from '@/types'

const INTERNAL_ROLES: UserRole[] = ['officer', 'auditor', 'admin']
const REVIEWER_ROLES: UserRole[] = ['officer', 'auditor', 'admin']

interface AuthContextValue {
  user: User | null
  initialising: boolean
  isAuthenticated: boolean
  isInternal: boolean
  isReviewer: boolean
  isAdmin: boolean
  signIn: (email: string, password: string) => Promise<User>
  adoptSession: (token: TokenResponse) => User
  signOut: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [initialising, setInitialising] = useState(true)

  useEffect(() => {
    let active = true
    if (!tokenStore.access) {
      setInitialising(false)
      return
    }
    authApi
      .me()
      .then((value) => {
        if (active) setUser(value)
      })
      .catch(() => {
        tokenStore.clear()
        if (active) setUser(null)
      })
      .finally(() => {
        if (active) setInitialising(false)
      })
    return () => {
      active = false
    }
  }, [])

  const adoptSession = useCallback((token: TokenResponse) => {
    tokenStore.set(token.access_token, token.refresh_token)
    setUser(token.user)
    return token.user
  }, [])

  const signIn = useCallback(
    async (email: string, password: string) => {
      const token = await authApi.login(email, password)
      return adoptSession(token)
    },
    [adoptSession],
  )

  const signOut = useCallback(async () => {
    try {
      await authApi.logout()
    } catch {
      /* the token may already be expired - clearing locally is enough */
    }
    tokenStore.clear()
    setUser(null)
  }, [])

  const refreshUser = useCallback(async () => {
    if (!tokenStore.access) return
    try {
      setUser(await authApi.me())
    } catch {
      tokenStore.clear()
      setUser(null)
    }
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      initialising,
      isAuthenticated: user !== null,
      isInternal: user !== null && INTERNAL_ROLES.includes(user.role),
      isReviewer: user !== null && REVIEWER_ROLES.includes(user.role),
      isAdmin: user?.role === 'admin',
      signIn,
      adoptSession,
      signOut,
      refreshUser,
    }),
    [user, initialising, signIn, adoptSession, signOut, refreshUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside <AuthProvider>.')
  return context
}
