import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { User, Mail, Phone, School, Award, Flame, Check, Shield, Save } from 'lucide-react'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { useI18n } from '@/i18n/I18nProvider'
import LoadingSpinner from '@/components/LoadingSpinner'

export default function ProfilePage() {
  const { lang, setLang } = useI18n()
  const { user, updateUser } = useAuthStore()
  const queryClient = useQueryClient()

  const [name, setName] = useState(user?.name || '')
  const [email, setEmail] = useState(user?.email || '')
  const [phone, setPhone] = useState('')
  const [selectedLang, setSelectedLang] = useState(user?.preferred_lang || lang)
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  // Fetch full user details from /api/v1/auth/me
  const { data: meData, isLoading } = useQuery({
    queryKey: ['user-me-profile'],
    queryFn: async () => {
      const res = await api.get('/auth/me')
      if (res.data) {
        setName(res.data.name || '')
        setEmail(res.data.email || '')
        setPhone(res.data.phone || '')
        setSelectedLang(res.data.preferred_lang || 'en')
      }
      return res.data
    },
  })

  // If student, fetch student profile
  const { data: studentProfile } = useQuery({
    queryKey: ['student-profile', user?.id],
    queryFn: async () => {
      const res = await api.get(`/students/${user?.id}/profile`)
      return res.data
    },
    enabled: user?.role === 'student',
  })

  // Update profile mutation
  const updateProfileMutation = useMutation({
    mutationFn: async () => {
      setSaveError(null)
      const res = await api.patch('/auth/me', {
        name: name.trim(),
        email: email.trim() || null,
        phone: phone.trim() || null,
        preferred_lang: selectedLang,
      })
      return res.data
    },
    onSuccess: (data) => {
      updateUser({
        name: data.name,
        email: data.email,
        preferred_lang: data.preferred_lang,
      })
      setLang(data.preferred_lang)
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 3000)
      queryClient.invalidateQueries({ queryKey: ['user-me-profile'] })
    },
    onError: (err: any) => {
      setSaveError(err.response?.data?.detail || 'Failed to update profile.')
    },
  })

  if (isLoading) return <LoadingSpinner />

  return (
    <div className="p-4 lg:p-8 max-w-5xl mx-auto space-y-6">
      <div className="border-b border-[#ccd5ae] pb-4">
        <h1 className="text-2xl font-black text-[#000000] flex items-center gap-2">
          <User className="w-6 h-6 text-[#000000]" />
          Profile & Account Settings
        </h1>
        <p className="text-xs sm:text-sm text-[#333333] mt-1">
          Manage your personal information, grade details, and preferred learning language.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column: Profile Card */}
        <div className="md:col-span-1 space-y-6">
          <div className="card p-6 text-center bg-white border border-[#ccd5ae] shadow-xs">
            <div className="w-20 h-20 rounded-full bg-[#faedcd] text-[#000000] font-black text-2xl flex items-center justify-center mx-auto border-2 border-[#ccd5ae]">
              {user?.username?.charAt(0).toUpperCase()}
            </div>
            <h2 className="text-lg font-bold text-[#000000] mt-4">{name || user?.username}</h2>
            <p className="text-xs text-[#333333]">@{user?.username}</p>
            <div className="mt-2.5">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-[#e9edc9] text-[#000000] border border-[#ccd5ae]">
                <Shield className="w-3.5 h-3.5 text-[#000000]" />
                {user?.role?.replace('_', ' ')}
              </span>
            </div>

            {studentProfile && (
              <div className="mt-6 pt-6 border-t border-[#ccd5ae] grid grid-cols-2 gap-3 text-left">
                <div className="p-2.5 rounded-lg bg-[#faedcd]/40 border border-[#ccd5ae]">
                  <div className="text-[11px] text-[#333333] flex items-center gap-1 font-medium">
                    <Award className="w-3.5 h-3.5 text-[#000000]" /> Class
                  </div>
                  <div className="text-sm font-bold text-[#000000] mt-0.5">
                    Class {studentProfile.grade}-{studentProfile.section}
                  </div>
                </div>
                <div className="p-2.5 rounded-lg bg-[#faedcd]/40 border border-[#ccd5ae]">
                  <div className="text-[11px] text-[#333333] flex items-center gap-1 font-medium">
                    <Flame className="w-3.5 h-3.5 text-[#d4a373]" /> Streak
                  </div>
                  <div className="text-sm font-bold text-[#000000] mt-0.5">
                    {studentProfile.current_streak} Days
                  </div>
                </div>
                <div className="col-span-2 p-2.5 rounded-lg bg-[#faedcd] border border-[#ccd5ae] text-[#000000]">
                  <div className="text-[11px] font-bold text-[#333333] uppercase">Total Mastery XP</div>
                  <div className="text-base font-black mt-0.5">{studentProfile.total_xp} XP</div>
                </div>
              </div>
            )}
          </div>

          <div className="card p-5 space-y-3 bg-white border border-[#ccd5ae]">
            <h3 className="text-xs font-bold uppercase tracking-wider text-[#000000]">Institution & Curriculum</h3>
            <div className="flex items-center gap-3 text-xs text-[#000000]">
              <School className="w-4 h-4 text-[#000000] shrink-0" />
              <div>
                <div className="font-bold text-[#000000]">{studentProfile?.school_name || 'CHATUR Educational Platform'}</div>
                <div className="text-[11px] text-[#333333]">Central Board of Secondary Education (CBSE)</div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Edit Profile Form */}
        <div className="md:col-span-2 space-y-6">
          <div className="card bg-white border border-[#ccd5ae]">
            <div className="card-header bg-[#faedcd]/40 border-b border-[#ccd5ae] p-4 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-[#000000]">Account Details</h3>
                <p className="text-xs text-[#333333]">Update your personal information and language preference.</p>
              </div>
              {saveSuccess && (
                <span className="inline-flex items-center gap-1.5 text-xs font-bold text-[#000000] bg-[#e9edc9] px-3 py-1 rounded-full border border-[#ccd5ae]">
                  <Check className="w-3.5 h-3.5 text-[#000000]" /> Saved successfully
                </span>
              )}
            </div>

            <div className="p-6 space-y-4">
              {saveError && (
                <div className="p-3 rounded-lg bg-rose-50 border border-rose-300 text-xs text-rose-900 font-medium">
                  {saveError}
                </div>
              )}

              <div>
                <label className="label text-xs font-bold text-[#000000]">Full Name</label>
                <div className="relative mt-1">
                  <User className="w-4 h-4 text-[#333333] absolute left-3 top-3" />
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="input-field pl-9 bg-white border border-[#ccd5ae] text-[#000000]"
                    placeholder="Enter your full name"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="label text-xs font-bold text-[#000000]">Email Address</label>
                  <div className="relative mt-1">
                    <Mail className="w-4 h-4 text-[#333333] absolute left-3 top-3" />
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="input-field pl-9 bg-white border border-[#ccd5ae] text-[#000000]"
                      placeholder="name@example.com"
                    />
                  </div>
                </div>

                <div>
                  <label className="label text-xs font-bold text-[#000000]">Phone Number</label>
                  <div className="relative mt-1">
                    <Phone className="w-4 h-4 text-[#333333] absolute left-3 top-3" />
                    <input
                      type="tel"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      className="input-field pl-9 bg-white border border-[#ccd5ae] text-[#000000]"
                      placeholder="+91 98765 43210"
                    />
                  </div>
                </div>
              </div>

              <div>
                <label className="label text-xs font-bold text-[#000000]">Preferred Learning Language</label>
                <div className="grid grid-cols-3 gap-3 mt-1">
                  {[
                    { id: 'en', label: 'English', native: 'English' },
                    { id: 'te', label: 'Telugu', native: 'తెలుగు' },
                    { id: 'hi', label: 'Hindi', native: 'हिन्दी' },
                  ].map((l) => (
                    <button
                      key={l.id}
                      type="button"
                      onClick={() => setSelectedLang(l.id as any)}
                      className={`p-3 rounded-xl border text-center transition-all cursor-pointer ${
                        selectedLang === l.id
                          ? 'bg-[#faedcd] border-2 border-[#d4a373] text-[#000000] font-bold shadow-xs'
                          : 'bg-white border-[#ccd5ae] text-[#000000] hover:bg-[#e9edc9]/50'
                      }`}
                    >
                      <div className="font-bold text-sm text-[#000000]">{l.native}</div>
                      <div className="text-xs text-[#333333] mt-0.5">
                        {l.label}
                      </div>
                    </button>
                  ))}
                </div>
                <p className="text-[11px] text-[#333333] mt-2">
                  Lesson explanations and practice hints will be served in this language when translations are available.
                </p>
              </div>

              <div className="pt-4 border-t border-[#ccd5ae] flex justify-end">
                <button
                  type="button"
                  onClick={() => updateProfileMutation.mutate()}
                  disabled={updateProfileMutation.isPending}
                  className="btn-primary text-xs px-5 py-2 font-bold flex items-center gap-1.5 cursor-pointer"
                >
                  <Save className="w-4 h-4 text-[#000000]" />
                  <span>{updateProfileMutation.isPending ? 'Saving…' : 'Save Changes'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
