import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import api from '@/lib/api'
import { BookOpen, Eye, EyeOff, AlertCircle, CheckCircle2, ArrowRight, KeyRound, Copy, Check } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useI18n } from '@/i18n/I18nProvider'
import type { Lang } from '@/i18n/translations'
import { formatLang } from '@/i18n/translations'

type Role = 'student' | 'teacher' | 'parent' | 'admin'
type AuthMode = 'login' | 'register' | 'forgot' | 'reset'

interface DemoAccount {
  role: Role
  label: string
  username: string
  password: string
}

const DEMO_ACCOUNTS: DemoAccount[] = [
  {
    role: 'admin',
    label: 'Admin',
    username: 'admin',
    password: 'Admin@School2024',
  },
  {
    role: 'student',
    label: 'Student',
    username: 'student1',
    password: 'Student@2024',
  },
  {
    role: 'teacher',
    label: 'Teacher',
    username: 'teacher1',
    password: 'Teacher@2024',
  },
  {
    role: 'parent',
    label: 'Parent',
    username: 'parent1',
    password: 'Parent@2024',
  },
]

const ROLE_ROUTES: Record<string, string> = {
  student: '/student',
  teacher: '/teacher',
  parent: '/parent',
  admin: '/admin',
  super_admin: '/admin',
}

export default function LoginPage() {
  const { t, lang, setLang } = useI18n()
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)

  const [mode, setMode] = useState<AuthMode>('login')
  const [role, setRole] = useState<Role>('student')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [grade, setGrade] = useState<number>(10)
  const [section, setSection] = useState('A')
  const [linkedStudent, setLinkedStudent] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [showPw, setShowPw] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [copiedRole, setCopiedRole] = useState<string | null>(null)

  const handleCopyCredentials = (e: React.MouseEvent, demo: DemoAccount) => {
    e.stopPropagation()
    if (navigator?.clipboard?.writeText) {
      navigator.clipboard.writeText(`Username: ${demo.username}\nPassword: ${demo.password}`)
    }
    setCopiedRole(demo.role)
    setTimeout(() => {
      setCopiedRole(null)
    }, 1500)
  }

  const handleSelectDemo = (demo: DemoAccount) => {
    setRole(demo.role)
    setUsername(demo.username)
    setPassword(demo.password)
    setErrorMsg(null)
  }

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: async () => {
      setErrorMsg(null)
      const { data } = await api.post('/auth/login', { username: username.trim(), password })
      return data
    },
    onSuccess: (data) => {
      setAuth(data.user, data.access_token, data.refresh_token)
      navigate(ROLE_ROUTES[data.user.role] ?? '/login')
    },
    onError: (err: any) => {
      setErrorMsg(err?.response?.data?.detail || 'Invalid username or password. Please try again.')
    },
  })

  // Register mutation
  const registerMutation = useMutation({
    mutationFn: async () => {
      setErrorMsg(null)
      const payload: Record<string, unknown> = {
        username: username.trim(),
        password,
        name: name.trim() || username.trim(),
        email: email.trim() || undefined,
        role,
        preferred_lang: lang,
      }
      if (role === 'student') {
        payload.grade = Number(grade)
        payload.section = section.trim().toUpperCase() || 'A'
      } else if (role === 'parent' && linkedStudent.trim()) {
        payload.linked_student_username = linkedStudent.trim()
      }
      const { data } = await api.post('/auth/register', payload)
      return data
    },
    onSuccess: (data) => {
      setAuth(data.user, data.access_token, data.refresh_token)
      navigate(ROLE_ROUTES[data.user.role] ?? '/login')
    },
    onError: (err: any) => {
      setErrorMsg(err?.response?.data?.detail || 'Registration failed. Please check your inputs.')
    },
  })

  // Forgot password mutation
  const forgotMutation = useMutation({
    mutationFn: async () => {
      setErrorMsg(null)
      setMessage(null)
      const { data } = await api.post('/auth/forgot-password', {
        username_or_email: username.trim() || email.trim(),
      })
      return data
    },
    onSuccess: (data) => {
      setMessage(data.message)
      setMode('reset')
    },
    onError: (err: any) => {
      setErrorMsg(err?.response?.data?.detail || 'Account not found.')
    },
  })

  // Reset password mutation
  const resetMutation = useMutation({
    mutationFn: async () => {
      setErrorMsg(null)
      setMessage(null)
      const { data } = await api.post('/auth/reset-password', {
        username: username.trim(),
        new_password: newPassword,
      })
      return data
    },
    onSuccess: (data) => {
      setMessage(data.message)
      setMode('login')
      setPassword('')
    },
    onError: (err: any) => {
      setErrorMsg(err?.response?.data?.detail || 'Failed to reset password.')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (mode === 'login') {
      loginMutation.mutate()
    } else if (mode === 'register') {
      registerMutation.mutate()
    } else if (mode === 'forgot') {
      forgotMutation.mutate()
    } else if (mode === 'reset') {
      resetMutation.mutate()
    }
  }

  const LANGS: Lang[] = ['en', 'te', 'hi']

  return (
    <div className="min-h-screen bg-[#fefae0] flex flex-col justify-center items-center p-4 text-[#000000]">
      {/* Top Language Bar */}
      <div className="w-full max-w-md flex justify-between items-center mb-6 px-1">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded bg-[#ccd5ae] border border-[#ccd5ae] flex items-center justify-center">
            <BookOpen className="w-4 h-4 text-[#000000]" />
          </div>
          <span className="font-bold tracking-tight text-lg text-[#000000]">CHATUR</span>
        </div>

        <div className="flex items-center bg-white border border-[#ccd5ae] rounded-lg p-0.5 text-xs text-[#000000]">
          {LANGS.map((l) => (
            <button
              key={l}
              onClick={() => setLang(l)}
              className={`px-2.5 py-0.5 rounded-md font-medium transition-all cursor-pointer ${lang === l
                ? 'bg-[#ccd5ae] text-[#000000] font-bold shadow-2xs'
                : 'text-[#333333] hover:bg-[#e9edc9]'
                }`}
            >
              {formatLang(l)}
            </button>
          ))}
        </div>
      </div>

      {/* Main Auth Card */}
      <div className="w-full max-w-md bg-white border border-[#ccd5ae] rounded-lg shadow-sm overflow-hidden text-[#000000]">
        {/* Card Header */}
        <div className="p-5 border-b border-[#ccd5ae] bg-[#faedcd]/40">
          <div className="flex items-center justify-between mb-2">
            <h1 className="text-lg font-bold text-[#000000]">
              {mode === 'login' && 'Sign In to Your Account'}
              {mode === 'register' && 'Create New Account'}
              {mode === 'forgot' && 'Reset Your Password'}
              {mode === 'reset' && 'Set New Password'}
            </h1>
            <span className="text-xs text-[#333333] font-medium">CBSE / NCERT</span>
          </div>
          <p className="text-xs text-[#333333]">
            {mode === 'login' && 'Enter your credentials to continue your curriculum study.'}
            {mode === 'register' && 'Select your role and start your personalized learning journey.'}
            {mode === 'forgot' && 'Enter your registered username or email address.'}
            {mode === 'reset' && 'Enter your username and new password.'}
          </p>
        </div>

        {/* Role Selector Tabs (Only on Login & Register) */}
        {(mode === 'login' || mode === 'register') && (
          <div className="px-5 pt-4">
            <label className="block text-xs font-semibold text-[#000000] mb-1.5">
              Select Account Role
            </label>
            <div className="grid grid-cols-4 gap-1.5 p-1 bg-[#fefae0] border border-[#ccd5ae] rounded-lg text-xs">
              {(['student', 'teacher', 'parent', 'admin'] as Role[]).map((r) => (
                <button
                  key={r}
                  type="button"
                  onClick={() => setRole(r)}
                  className={`py-1.5 rounded-md font-semibold transition-all capitalize cursor-pointer text-center ${role === r
                    ? 'bg-[#ccd5ae] text-[#000000] shadow-2xs border border-[#ccd5ae]'
                    : 'text-[#333333] hover:bg-[#e9edc9]'
                    }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Error / Success Messages */}
        <div className="px-5 pt-3">
          {errorMsg && (
            <div className="p-2.5 rounded-md bg-red-50 border border-red-300 text-xs text-red-900 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-600 mt-0.5" />
              <span>{errorMsg}</span>
            </div>
          )}
          {message && (
            <div className="p-2.5 rounded-md bg-emerald-50 border border-emerald-300 text-xs text-emerald-900 flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600 mt-0.5" />
              <span>{message}</span>
            </div>
          )}
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-5 space-y-3.5">
          {mode === 'register' && (
            <div>
              <label className="label">Full Name</label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Aarav Patel"
                className="input-field"
              />
            </div>
          )}

          <div>
            <label className="label">Username</label>
            <input
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. student1 or your unique username"
              className="input-field"
            />
          </div>

          {(mode === 'register' || mode === 'forgot') && (
            <div>
              <label className="label">Email Address (Optional)</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="e.g. user@example.com"
                className="input-field"
              />
            </div>
          )}

          {/* Student Specific Fields */}
          {mode === 'register' && role === 'student' && (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">Class / Grade</label>
                <select
                  value={grade}
                  onChange={(e) => setGrade(Number(e.target.value))}
                  className="input-field"
                >
                  <option value={6}>Class 6</option>
                  <option value={7}>Class 7</option>
                  <option value={8}>Class 8</option>
                  <option value={9}>Class 9</option>
                  <option value={10}>Class 10</option>
                </select>
              </div>
              <div>
                <label className="label">Section</label>
                <input
                  type="text"
                  maxLength={2}
                  value={section}
                  onChange={(e) => setSection(e.target.value)}
                  placeholder="A"
                  className="input-field uppercase"
                />
              </div>
            </div>
          )}

          {/* Parent Specific Field */}
          {mode === 'register' && role === 'parent' && (
            <div>
              <label className="label">Child's Student Username</label>
              <input
                type="text"
                value={linkedStudent}
                onChange={(e) => setLinkedStudent(e.target.value)}
                placeholder="Username of your student (e.g. student1)"
                className="input-field"
              />
              <p className="text-[11px] text-[#666666] mt-1">
                Parent accounts view progress for verified linked students.
              </p>
            </div>
          )}

          {/* Password field for Login & Register */}
          {(mode === 'login' || mode === 'register') && (
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-xs font-semibold text-[#000000]">Password</label>
                {mode === 'login' && (
                  <button
                    type="button"
                    onClick={() => { setMode('forgot'); setErrorMsg(null); setMessage(null); }}
                    className="text-xs text-[#333333] hover:text-[#000000] underline cursor-pointer"
                  >
                    Forgot password?
                  </button>
                )}
              </div>
              <div className="relative">
                <input
                  type={showPw ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="input-field pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#666666] hover:text-[#000000] cursor-pointer"
                >
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
          )}

          {/* New Password for Reset Mode */}
          {mode === 'reset' && (
            <div>
              <label className="label">New Password</label>
              <input
                type="password"
                required
                minLength={6}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="At least 6 characters"
                className="input-field"
              />
            </div>
          )}

          {/* Action Button */}
          <div className="pt-2">
            <button
              type="submit"
              disabled={loginMutation.isPending || registerMutation.isPending || forgotMutation.isPending || resetMutation.isPending}
              className="w-full btn-primary py-2.5 text-sm"
            >
              {loginMutation.isPending || registerMutation.isPending || forgotMutation.isPending || resetMutation.isPending
                ? 'Processing…'
                : mode === 'login'
                  ? 'Sign In'
                  : mode === 'register'
                    ? 'Create Account'
                    : mode === 'forgot'
                      ? 'Verify Account'
                      : 'Save New Password'}
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </form>

        {/* Demo Credentials for Evaluators */}
        {mode === 'login' && (
          <div className="px-5 pb-5">
            <div className="pt-3.5 border-t border-[#ccd5ae]">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-1.5">
                  <KeyRound className="w-3.5 h-3.5 text-[#d4a373]" />
                  <span className="text-xs font-bold text-[#000000]">
                    Demo Credentials (for Evaluators)
                  </span>
                </div>
                <span className="text-[10px] text-[#333333] bg-[#faedcd] px-2 py-0.5 rounded-full border border-[#ccd5ae] font-bold">
                  Click to auto-fill
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2">
                {DEMO_ACCOUNTS.map((demo) => {
                  const isSelected = username === demo.username && role === demo.role && password === demo.password
                  const isCopied = copiedRole === demo.role

                  return (
                    <div
                      key={demo.role}
                      role="button"
                      tabIndex={0}
                      onClick={() => handleSelectDemo(demo)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault()
                          handleSelectDemo(demo)
                        }
                      }}
                      title={`Click to auto-fill ${demo.label} credentials`}
                      className={`p-2.5 rounded-lg border text-left transition-all cursor-pointer relative ${isSelected
                        ? 'bg-[#e9edc9] border-[#ccd5ae] ring-2 ring-[#d4a373]/60 shadow-xs'
                        : 'bg-[#fefae0]/80 hover:bg-[#faedcd]/70 border-[#ccd5ae]'
                        }`}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="font-bold text-xs text-[#000000] flex items-center gap-1.5">
                          <span
                            className={`w-2 h-2 rounded-full ${isSelected ? 'bg-emerald-600' : 'bg-[#d4a373]'
                              }`}
                          />
                          {demo.label}
                        </span>

                        <div className="flex items-center gap-1">
                          {isSelected && (
                            <span className="text-[9px] font-bold text-emerald-800 bg-emerald-100 px-1 py-0.2 rounded border border-emerald-300">
                              Active
                            </span>
                          )}
                          <button
                            type="button"
                            onClick={(e) => handleCopyCredentials(e, demo)}
                            title="Copy username and password"
                            className="p-1 rounded hover:bg-white/80 text-[#666666] hover:text-[#000000] transition-colors cursor-pointer"
                          >
                            {isCopied ? (
                              <Check className="w-3 h-3 text-emerald-600" />
                            ) : (
                              <Copy className="w-3 h-3" />
                            )}
                          </button>
                        </div>
                      </div>

                      <div className="space-y-0.5 text-[11px] leading-tight select-text">
                        <div className="flex items-baseline justify-between text-[#333333]">
                          <span className="text-[10px] text-[#666666] font-medium">User:</span>
                          <span className="font-mono font-semibold text-[#000000]">{demo.username}</span>
                        </div>
                        <div className="flex items-baseline justify-between text-[#333333]">
                          <span className="text-[10px] text-[#666666] font-medium">Pass:</span>
                          <span className="font-mono font-semibold text-[#000000] text-[10.5px]">
                            {demo.password}
                          </span>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        )}

        {/* Mode Toggle Footer */}
        <div className="p-4 border-t border-[#ccd5ae] bg-[#faedcd]/20 text-center text-xs text-[#333333]">
          {mode === 'login' ? (
            <p>
              Don't have an account?{' '}
              <button
                type="button"
                onClick={() => { setMode('register'); setErrorMsg(null); setMessage(null); }}
                className="font-bold text-[#000000] underline hover:text-[#d4a373] cursor-pointer ml-1"
              >
                Register Now
              </button>
            </p>
          ) : (
            <p>
              Already have an account?{' '}
              <button
                type="button"
                onClick={() => { setMode('login'); setErrorMsg(null); setMessage(null); }}
                className="font-bold text-[#000000] underline hover:text-[#d4a373] cursor-pointer ml-1"
              >
                Sign In
              </button>
            </p>
          )}
        </div>
      </div>

      {/* Footer Branding */}
      <div className="mt-6 text-center text-xs text-[#666666]">
        CHATUR — CBSE / NCERT Educational Platform &copy; 2026
      </div>
    </div>
  )
}
