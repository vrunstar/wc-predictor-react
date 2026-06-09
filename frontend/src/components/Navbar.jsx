import React, { useState, useEffect } from 'react';
import { NavLink, Link, useLocation } from 'react-router-dom';
import { Menu, X, Shield } from 'lucide-react';

const NAV_ITEMS = [
  { label: 'Predictions', path: '/predictions' },
  { label: 'Fixtures', path: '/fixtures' },
  { label: 'Results', path: '/results' },
  { label: 'Standings', path: '/standings' },
  { label: 'Knockouts', path: '/knockouts' }
];

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const location = useLocation();
  const isHome = location.pathname === '/';

  useEffect(() => {
    const handleScroll = () => {
      const threshold = isHome ? window.innerHeight * 0.3 : 20;
      setScrolled(window.scrollY > threshold);
    };
    handleScroll();
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [isHome]);

  const toggleMenu = () => setIsOpen(!isOpen);

  const activeClassName = "text-white bg-white/10 border-white/20 font-semibold";
  const inactiveClassName = "text-[#aaa] border-transparent hover:text-white hover:bg-white/5";

  return (
    <nav
      className={`fixed top-0 left-0 right-0 h-[60px] z-[9999] transition-all duration-500 ${
        isHome && !scrolled ? 'opacity-0 pointer-events-none' : 'opacity-100'
      }`}
      style={{
        backgroundImage: 'url(/navbar.png)',
        backgroundSize: 'cover',
        backgroundPosition: 'top center',
      }}
    >
      <div className="h-full px-4 md:px-8 flex items-center justify-between">

        {/* LEFT: Logo */}
        <Link to="/" className="flex items-center h-full">
          <img
            src="/logo.png"
            alt="Logo"
            className="h-[36px] w-auto block object-contain"
          />
        </Link>

        {/* CENTER: Nav links */}
        <div className="hidden md:flex items-center justify-center gap-1 absolute left-1/2 transform -translate-x-1/2">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.label}
              to={item.path}
              className={({ isActive }) =>
                `px-3.5 py-[6px] rounded-[6px] transition-all duration-150 border text-xs uppercase tracking-wider font-medium ${
                  isActive ? activeClassName : inactiveClassName
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </div>

        {/* RIGHT: Admin */}
        <div className="hidden md:flex items-center">
          <NavLink
            to="/admin"
            className={({ isActive }) =>
              `p-2 rounded-full border transition-all duration-150 ${
                isActive
                  ? 'text-white bg-white/10 border-white/20'
                  : 'text-[#aaa] border-transparent hover:text-white hover:bg-white/5'
              }`
            }
            title="Admin Panel"
          >
            <Shield size={18} />
          </NavLink>
        </div>

        {/* Mobile toggles */}
        <div className="flex items-center gap-2 md:hidden">
          <NavLink
            to="/admin"
            onClick={() => setIsOpen(false)}
            className={({ isActive }) =>
              `p-2 rounded-full border transition-all duration-150 ${
                isActive
                  ? 'text-white bg-white/10 border-white/20'
                  : 'text-[#aaa] border-transparent hover:text-white'
              }`
            }
          >
            <Shield size={18} />
          </NavLink>
          <button
            onClick={toggleMenu}
            className="text-[#aaa] hover:text-white p-2 focus:outline-none"
            aria-label="Toggle navigation menu"
          >
            {isOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {/* Mobile Dropdown */}
      {isOpen && (
        <div
          className="absolute top-[60px] left-0 right-0 border-b border-white/4 flex flex-col py-2 md:hidden"
          style={{
            backgroundImage: 'url(/bg-mobile.png)',
            backgroundSize: 'cover',
            backgroundPosition: 'center',
          }}
        >
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.label}
              to={item.path}
              onClick={() => setIsOpen(false)}
              className={({ isActive }) =>
                `px-6 py-3 border-b border-white/5 text-[0.95rem] transition-all duration-150 uppercase tracking-wider text-xs font-semibold ${
                  isActive ? 'text-white bg-white/10' : 'text-[#ccc] hover:bg-white/5'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </div>
      )}
    </nav>
  );
}
