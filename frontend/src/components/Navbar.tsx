import React, { useState } from "react";
import logo from "../assets/images/logo.png";
import { navItems } from "../constants";
import { Link } from "react-router-dom";
import { Menu, X, Search } from "lucide-react";
import { FaUserCircle } from "react-icons/fa";
import { motion, AnimatePresence } from "framer-motion";

const Navbar = () => {
  const [open, setOpen] = useState(false);

  return (
    <header className="fixed top-0 left-0 right-0 z-50 border-b border-gray-200 shadow-sm bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <nav className="flex items-center justify-between h-16">
          {/* Logo + Title */}
          <div className="flex items-center space-x-2">
            <img src={logo} alt="logo" className="w-8 h-8 object-contain" />
            <h1 className="text-xl font-bold text-gray-800">LawLens</h1>
          </div>

          {/* Desktop Navigation */}
          <ul className="hidden lg:flex flex-1 justify-center items-center space-x-6">
            {navItems.map((item, index) => (
              <li key={index}>
                <Link
                  to={item.path}
                  className="text-gray-700 hover:text-primary font-medium transition-colors duration-200"
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
              <Search className="absolute left-2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search..."
                className="pl-8 pr-3 py-1.5 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary text-sm"
              />
            </div>

            {/* User Icon (no dropdown) */}
            <Link to="/profile">
            <FaUserCircle className="w-8 h-8 text-gray-600 hover:text-primary cursor-pointer" />
            </Link>
            

            {/* Mobile/Tablet Menu Icon */}
            <div className="lg:hidden">
              <button onClick={() => setOpen(!open)} className="text-gray-800">
                {open ? <X size={24} /> : <Menu size={24} />}
              </button>
            </div>
          </div>
        </nav>

        {/* Mobile/Tablet Dropdown */}
        <AnimatePresence>
          {open && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3 }}
              className="lg:hidden mt-2 space-y-2 pb-4"
            >
              {navItems.map((item, index) => (
                <Link
                  key={index}
                  to={item.path}
                  onClick={() => setOpen(false)}
                  className="block px-2 py-1 text-gray-700 hover:text-primary font-medium transition"
                >
                  {item.label}
                </Link>
              ))}

              {/* Mobile/Tablet search */}
              <div className="flex items-center mt-2 px-2">
                <Search size={16} color="#9ca3af" className="mr-2" />
                <input
                  type="text"
                  placeholder="Search..."
                  className="flex-1 px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
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
