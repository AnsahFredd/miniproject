import React, { useState } from "react";
// import logo from "../assets/images/logo.png";
import { navItems } from "../constants";
import { Link } from "react-router-dom";
import { Menu, X, Search } from 'lucide-react';
import { FaUserCircle } from "react-icons/fa";
import { motion, AnimatePresence } from "framer-motion";

const Navbar = () => {
  const [open, setOpen] = useState(false);

  return (
    <header 
      className="fixed top-0 left-0 right-0 z-50 nav-elevated"
      role="banner"
    >
      <div className="max-w-7xl mx-auto px-4 py-2.5 items-center justify-center sm:px-6 lg:px-8">
        <nav className="flex items-center justify-between h-16" aria-label="Main Navigation">
          {/* Logo + Title */}
          <div className="flex items-center space-x-2">
            {/* <img src={logo || "/placeholder.svg"} alt="LawLens logo" className="w-8 h-8 object-contain" /> */}
            <h1 className="text-xl font-bold text-[var(--color-primary)]">
              LawLens
            </h1>
          </div>

          {/* Desktop Navigation */}
          <ul className="hidden lg:flex flex-1 justify-center items-center space-x-6">
            {navItems.map((item, index) => (
              <li key={index}>
                <Link
                  to={item.path}
                  className="font-medium text-[var(--color-secondary)] hover:text-[var(--color-primary)] transition-colors duration-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--color-accent)] focus-visible:outline-offset-2"
                >
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>

          {/* Search + User + Menu */}
          <div className="flex items-center space-x-4">
            {/* Desktop Search */}
            <div className="hidden lg:flex items-center relative">
              <label htmlFor="global-search" className="sr-only">Search</label>
              <Search 
                className="absolute left-3 w-4 h-4 text-[var(--color-secondary)]/70" 
                aria-hidden="true"
              />
              <input
                id="global-search"
                type="text"
                placeholder="Search..."
                className="pl-9 pr-3 py-2 border rounded-md text-sm input h-10"
              />
            </div>

            {/* User Icon */}
            <Link to="/profile" aria-label="Profile">
              <FaUserCircle 
                className="w-8 h-8 cursor-pointer text-[var(--color-primary)] hover:opacity-80 transition-colors" 
              />
            </Link>

            {/* Mobile/Tablet Menu Icon */}
            <div className="lg:hidden">
              <button 
                onClick={() => setOpen(!open)} 
                className="transition-colors hover:opacity-80 text-[var(--color-primary)]"
                aria-expanded={open ? "true" : "false"}
                aria-controls="mobile-menu"
                aria-label="Toggle navigation"
              >
                {open ? <X size={24} /> : <Menu size={24} />}
              </button>
            </div>
          </div>
        </nav>

        {/* Mobile/Tablet Dropdown */}
        <AnimatePresence>
          {open && (
            <motion.div
              id="mobile-menu"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3 }}
              className="lg:hidden mt-2 space-y-2 pb-4"
              aria-label="Mobile Navigation"
            >
              {navItems.map((item, index) => (
                <Link
                  key={index}
                  to={item.path}
                  onClick={() => setOpen(false)}
                  className="block px-3 py-2 font-medium text-[var(--color-secondary)] hover:text-[var(--color-primary)] transition-colors"
                >
                  {item.label}
                </Link>
              ))}

              {/* Mobile/Tablet search */}
              <div className="flex items-center mt-2 px-2">
                <label htmlFor="mobile-search" className="sr-only">Search</label>
                <Search 
                  size={16} 
                  className="mr-2 text-[var(--color-secondary)]/70"
                  aria-hidden="true" 
                />
                <input
                  id="mobile-search"
                  type="text"
                  placeholder="Search..."
                  className="flex-1 px-3 py-2 input text-sm"
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </header>
  );
};

export default Navbar;
