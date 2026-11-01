import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import axios from 'axios'
import { BookOpen, Eye, EyeOff } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useI18n } from '@/i18n/I18nProvider'
import type { Lang } from '@/i18n/translations'
import { formatLang } from '@/i18n/translations'

type Role = 'student' | 'teacher' | 'parent' | 'admin'

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

  const [role, setRole] = useState<Role>('student')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPw, setShowPw] = useState(false)

  const loginMutation = useMutation({
    mutationFn: async () => {
      const { data } = await axios.post('/api/v1/auth/login', { username, password })
      return data
    },
    onSuccess: (data) => {
      setAuth(data.user, data.access_token, data.refresh_token)
      navigate(ROLE_ROUTES[data.user.role] ?? '/login')
    },
  })

  const roles: { value: Role; label: string }[] = [
    { value: 'student', label: t('role_student') },
    { value: 'teacher', label: t('role_teacher') },
    { value: 'parent', label: t('role_parent') },
    { value: 'admin', label: t('role_admin') },
  ]

  const LANGS: Lang[] = ['en', 'te', 'hi']

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-900 via-primary-800 to-accent-700 flex items-center justify-center p-4">
      {/* Language switcher */}
      <div className="absolute top-4 right-4 flex gap-2">
        {LANGS.map((l) => (
          <button
            key={l}
            onClick={() => setLang(l)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              lang === l
                ? 'bg-white text-primary-800'
                : 'bg-white/20 text-white hover:bg-white/30'
            }`}
          >
            {formatLang(l)}
          </button>
        ))}
      </div>

      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white/10 rounded-2xl mb-4">
            <BookOpen className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight">{t('app_name')}</h1>
          <p className="mt-2 text-primary-200 text-sm leading-relaxed max-w-xs mx-auto">
            {t('app_tagline')}
          </p>
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <h2 className="text-lg font-semibold text-slate-900 mb-6">{t('sign_in')}</h2>

          {/* Role tabs */}
          <div className="grid grid-cols-2 gap-2 mb-6">
            {roles.map((r) => (
              <button
                key={r.value}
                onClick={() => setRole(r.value)}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  role === r.value
                    ? 'bg-primary-800 text-white shadow-sm'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {r.label}
              </button>
            ))}
          </div>

          {/* Form */}
          <form
            onSubmit={(e) => { e.preventDefault(); loginMutation.mutate() }}
            className="space-y-4"
          >
            <div>
              <label className="label">{t('username')}</label>
              <input
                className="input-field"
                type="text"
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>

            <div>
              <label className="label">{t('password')}</label>
              <div className="relative">
                <input
                  className="input-field pr-10"
                  type={showPw ? 'text' : 'password'}
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {loginMutation.isError && (
              <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                {t('login_error')}
              </p>
            )}

            <button
              type="submit"
              disabled={loginMutation.isPending}
              className="btn-primary w-full justify-center py-2.5"
            >
              {loginMutation.isPending ? t('signing_in') : t('sign_in')}
            </button>
          </form>

          {/* Demo credentials hint */}
          <div className="mt-6 pt-5 border-t border-slate-100">
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-3">Demo Accounts</p>
            <div className="grid grid-cols-2 gap-2 text-xs text-slate-600">
              <div className="bg-slate-50 rounded-lg p-2">
                <div className="font-medium">Student</div>
                <div className="text-slate-500">student1 / Student@2024</div>
              </div>
              <div className="bg-slate-50 rounded-lg p-2">
                <div className="font-medium">Teacher</div>
                <div className="text-slate-500">teacher1 / Teacher@2024</div>
              </div>
              <div className="bg-slate-50 rounded-lg p-2">
                <div className="font-medium">Parent</div>
                <div className="text-slate-500">parent1 / Parent@2024</div>
              </div>
              <div className="bg-slate-50 rounded-lg p-2">
                <div className="font-medium">Admin</div>
                <div className="text-slate-500">admin / Admin@School2024</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
