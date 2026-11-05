import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import LoginPage from './pages/LoginPage'
import StudentLayout from './layouts/StudentLayout'
import TeacherLayout from './layouts/TeacherLayout'
import ParentLayout from './layouts/ParentLayout'
import AdminLayout from './layouts/AdminLayout'
import StudentDashboard from './pages/student/StudentDashboard'
import StudentLearn from './pages/student/StudentLearn'
import StudentSolve from './pages/student/StudentSolve'
import StudentPractice from './pages/student/StudentPractice'
import StudentTest from './pages/student/StudentTest'
import StudentProgress from './pages/student/StudentProgress'
import StudentTodoList from './pages/student/StudentTodoList'
import ProfilePage from './pages/ProfilePage'
import TeacherDashboard from './pages/teacher/TeacherDashboard'
import TeacherHeatmap from './pages/teacher/TeacherHeatmap'
import TeacherReviewQueue from './pages/teacher/TeacherReviewQueue'
import TeacherGroups from './pages/teacher/TeacherGroups'
import TeacherContent from './pages/teacher/TeacherContent'
import TeacherImpact from './pages/teacher/TeacherImpact'
import ParentDashboard from './pages/parent/ParentDashboard'
import AdminDashboard from './pages/admin/AdminDashboard'
import AdminUsers from './pages/admin/AdminUsers'
import AdminCurriculum from './pages/admin/AdminCurriculum'
import AdminSchools from './pages/admin/AdminSchools'

function RequireAuth({ children, roles }: { children: React.ReactNode; roles: string[] }) {
  const user = useAuthStore((s) => s.user)
  if (!user) return <Navigate to="/login" replace />
  if (!roles.includes(user.role)) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        {/* Student routes */}
        <Route path="/student" element={
          <RequireAuth roles={['student']}>
            <StudentLayout />
          </RequireAuth>
        }>
          <Route index element={<StudentDashboard />} />
          <Route path="dashboard" element={<StudentDashboard />} />
          <Route path="learn" element={<StudentLearn />} />
          <Route path="solve" element={<StudentSolve />} />
          <Route path="practice" element={<StudentPractice />} />
          <Route path="test" element={<StudentTest />} />
          <Route path="progress" element={<StudentProgress />} />
          <Route path="tasks" element={<StudentTodoList />} />
          <Route path="profile" element={<ProfilePage />} />
        </Route>

        {/* Teacher routes */}
        <Route path="/teacher" element={
          <RequireAuth roles={['teacher']}>
            <TeacherLayout />
          </RequireAuth>
        }>
          <Route index element={<TeacherDashboard />} />
          <Route path="dashboard" element={<TeacherDashboard />} />
          <Route path="learn" element={<StudentLearn />} />
          <Route path="practice" element={<StudentPractice />} />
          <Route path="test" element={<StudentTest />} />
          <Route path="heatmap" element={<TeacherHeatmap />} />
          <Route path="review" element={<TeacherReviewQueue />} />
          <Route path="groups" element={<TeacherGroups />} />
          <Route path="content" element={<TeacherContent />} />
          <Route path="impact" element={<TeacherImpact />} />
          <Route path="profile" element={<ProfilePage />} />
        </Route>

        {/* Parent routes */}
        <Route path="/parent" element={
          <RequireAuth roles={['parent']}>
            <ParentLayout />
          </RequireAuth>
        }>
          <Route index element={<ParentDashboard />} />
          <Route path="dashboard" element={<ParentDashboard />} />
          <Route path="profile" element={<ProfilePage />} />
        </Route>

        {/* Admin routes */}
        <Route path="/admin" element={
          <RequireAuth roles={['admin', 'super_admin']}>
            <AdminLayout />
          </RequireAuth>
        }>
          <Route index element={<AdminDashboard />} />
          <Route path="dashboard" element={<AdminDashboard />} />
          <Route path="users" element={<AdminUsers />} />
          <Route path="curriculum" element={<AdminCurriculum />} />
          <Route path="schools" element={<AdminSchools />} />
          <Route path="profile" element={<ProfilePage />} />
        </Route>

        {/* Root redirect */}
        <Route path="/" element={<RootRedirect />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

function RootRedirect() {
  const user = useAuthStore((s) => s.user)
  if (!user) return <Navigate to="/login" replace />
  const map: Record<string, string> = {
    student: '/student',
    teacher: '/teacher',
    parent: '/parent',
    admin: '/admin',
    super_admin: '/admin',
  }
  return <Navigate to={map[user.role] ?? '/login'} replace />
}
