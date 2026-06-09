import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import { Shield } from 'lucide-react';

const NAV_ITEMS = [
  { label: 'Predictions', path: '/predictions', icon: '/icons/predictions.svg' },
  { label: 'Fixtures',    path: '/fixtures',    icon: '/icons/fixtures.svg'    },
  { label: 'Results',     path: '/results',     icon: '/icons/results.svg'     },
  { label: 'Standings',   path: '/standings',   icon: '/icons/standings.svg'   },
  { label: 'Knockouts',   path: '/knockouts',   icon: '/icons/knockouts.svg'   },
];

export default function Navbar() {
  return (
    <>
      {/* ── DESKTOP NAV ── */}
      <nav
        className="fixed top-0 left-0 right-0 h-[60px] z-[9999] hidden md:flex items-center justify-between px-[160px]"
        style={{
          backgroundImage: 'url(/navbar.png)',
          backgroundSize: 'cover',
          backgroundPosition: 'top center',
        }}
      >
        {/* Logo */}
        <Link to="/" className="flex items-center h-full">
          <img src="/logo.png" alt="Logo" className="h-[36px] w-auto object-contain" />
        </Link>

        {/* Right: links + divider + admin */}
        <div className="flex items-center gap-6">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.label}
              to={item.path}
              className={({ isActive }) =>
                `text-xs uppercase tracking-widest font-semibold font-inter transition-colors duration-150 pb-[2px] ${
                  isActive
                    ? 'text-white border-b-2 border-white'
                    : 'text-[#aaa] hover:text-white border-b-2 border-transparent'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}

          {/* Divider */}
          <div className="w-px h-4 bg-white/20" />

          {/* Admin */}
          <NavLink
            to="/admin"
            title="Admin Panel"
            className={({ isActive }) =>
              `transition-colors duration-150 ${isActive ? 'text-white' : 'text-[#aaa] hover:text-white'}`
            }
          >
            <Shield size={18} />
          </NavLink>
        </div>
      </nav>

      {/* ── MOBILE TOP BAR ── */}
      <div
        className="fixed top-0 left-0 right-0 h-[52px] z-[9999] flex md:hidden items-center justify-between px-4"
        style={{
          backgroundImage: 'url(/navbar.png)',
          backgroundSize: 'cover',
          backgroundPosition: 'top center',
        }}
      >
        <Link to="/">
          <img src="/logo.png" alt="Logo" className="h-[30px] w-auto object-contain" />
        </Link>
        <NavLink
          to="/admin"
          className={({ isActive }) =>
            `transition-colors duration-150 ${isActive ? 'text-white' : 'text-[#aaa] hover:text-white'}`
          }
        >
          <Shield size={18} />
        </NavLink>
      </div>

      {/* ── MOBILE BOTTOM NAV ── */}
      <nav className="fixed bottom-0 left-0 right-0 h-[60px] z-[9999] flex md:hidden items-center justify-around bg-[#0a0a0a] border-t border-white/8">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.label}
            to={item.path}
            className={({ isActive }) =>
              `flex flex-col items-center justify-center gap-[3px] flex-1 h-full transition-colors duration-150 ${
                isActive ? 'text-white' : 'text-[#555] hover:text-[#aaa]'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <img
                  src={item.icon}
                  alt={item.label}
                  className={`w-[20px] h-[20px] object-contain ${isActive ? 'opacity-100' : 'opacity-40'}`}
                />
                <span className={`text-[9px] uppercase tracking-widest font-semibold font-inter ${isActive ? 'text-white' : 'text-[#555]'}`}>
                  {item.label === 'Knockouts' ? 'KO' : item.label}
                </span>
                {isActive && <div className="absolute bottom-0 w-8 h-[2px] bg-white rounded-full" />}
              </>
            )}
          </NavLink>
        ))}
      </nav>
    </>
  );
}
