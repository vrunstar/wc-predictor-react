import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import { Shield } from 'lucide-react';

const NAV_ITEMS = [
  { label: 'Predictions', path: '/predictions', icon: '/icons/predictions.svg' },
  { label: 'Fixtures',    path: '/fixtures',    icon: '/icons/fixtures.svg'    },
  { label: 'Results',     path: '/results',     icon: '/icons/results.svg'     },
  { label: 'Standings',   path: '/standings',   icon: '/icons/standings.svg'   },
  { label: 'Knockouts',   path: '/knockouts',   icon: '/icons/ko.svg'   },
];

export default function Navbar() {
  return (
    <>
      {/* ── DESKTOP NAV ── */}
      <nav
        className="fixed top-0 left-0 right-0 h-[70px] z-[9999] hidden md:flex items-center justify-between px-[160px]"
        style={{
          backgroundColor: '#0a0a0a',
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
                `relative text-xs tracking-widest font-semibold font-inter transition-colors duration-150 ${
                  isActive
                    ? 'text-white after:absolute after:bottom-[-27px] after:left-0 after:right-0 after:h-[2px] after:bg-white'
                    : 'text-[#aaa] hover:text-white'
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
          backgroundColor: '#0a0a0a',
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
      <nav className="fixed bottom-0 left-0 right-0 h-[70px] z-[9999] flex md:hidden items-center justify-around bg-[#0a0a0a]">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.label}
            to={item.path}
                className={({ isActive }) =>
              `relative flex flex-col items-center justify-center gap-[3px] flex-1 h-full transition-colors duration-150 ${
                isActive ? 'text-white' : 'text-[#555] hover:text-[#aaa]'
              }`
            }
          >
            {({ isActive }) => (
              <>
                {isActive && <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-white" />}
                <img
                  src={item.icon}
                  alt={item.label}
                  className={`w-[25px] h-[25px] object-contain ${isActive ? 'opacity-100' : 'opacity-40'}`}
                />
                <span className={`text-[7.5px] tracking-widest font-medium font-inter ${isActive ? 'text-white' : 'text-[#555]'}`}>
                  {item.label === 'Knockouts' ? 'KO' : item.label}
                </span>
              </>
            )}
          </NavLink>
        ))}
      </nav>
    </>
  );
}
