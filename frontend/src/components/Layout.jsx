import { Outlet } from 'react-router-dom'
import Nav from './Nav'

export default function Layout() {
  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden">
      <Nav />
      <main className="flex-1 overflow-y-auto p-8">
        <Outlet />
      </main>
    </div>
  )
}
