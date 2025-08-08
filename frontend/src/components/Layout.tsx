import { Outlet, useLocation, Link } from "react-router-dom";
import Navbar from "./Navbar";
import Footer from "./Footer";
import { useAuth } from "../auth/AuthContext";
import { useState } from "react";
import { Menu, X, Search } from 'lucide-react';
import { motion, AnimatePresence } from "framer-motion";

const Layout = () => {
  const location = useLocation();
  const [open, setOpen] = useState(false);

  const path = location.pathname;

  const { token, loading } = useAuth();

  if (loading) return null;

  const isAuthPage =
    path === "/" ||
    path === "/login" ||
    path === "/signup" ||
    path === "/reset-password";

  const showSignupLogin = path === "/";
  const showLoginButton = path === "/signup" || path === "/reset-password";

  return (
    <div className="flex flex-col min-h-screen">
      {/* Skip link */}
      <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 btn btn-secondary h-10 px-3">
        Skip to content
      </a>

      {isAuthPage ? (
        <header className="fixed top-0 left-0 right-0 z-50 border-b border-gray-200 shadow-sm bg-white" role="banner">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <nav className="flex items-center justify-between h-18 bg-white" aria-label="Top Navigation">
              {/* Logo + Title */}
              <div className="flex items-center space-x-2">
                <h1 className="text-xl font-bold text-[var(--color-primary)]">LawLens</h1>
              </div>

              {/* Desktop Buttons */}
              {showSignupLogin && (
                <div className="hidden lg:flex items-center space-x-4">
                  <Link
                    to="/signup"
                    className="btn btn-secondary text-sm h-10"
                  >
                    Create an account
                  </Link>
                  <Link
                    to="/login"
                    className="btn btn-primary text-sm h-10"
                  >
                    Log in
                  </Link>
                </div>
              )}

              {showLoginButton && (
                <div className="hidden lg:flex">
                  <Link
                    to="/login"
                    className="btn btn-primary text-sm h-10"
                  >
                    Login
                  </Link>
                </div>
              )}

              {/* Mobile Hamburger */}
              <div className="lg:hidden">
                <button
                  onClick={() => setOpen(!open)}
                  className="text-[var(--color-primary)]"
                  aria-expanded={open ? "true" : "false"}
                  aria-controls="mobile-auth-menu"
                  aria-label="Toggle navigation"
                >
                  {open ? <X size={24} /> : <Menu size={24} />}
                </button>
              </div>
            </nav>

            {/* Mobile Dropdown */}
            <AnimatePresence>
              {open && (
                <motion.div
                  id="mobile-auth-menu"
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.3 }}
                  className="lg:hidden mt-2 space-y-2 pb-4"
                  aria-label="Mobile Navigation"
                >
                  {showSignupLogin && (
                    <>
                      <Link
                        to="/signup"
                        onClick={() => setOpen(false)}
                        className="btn btn-outline-accent mr-12 block px-4 py-2 bg-white text-[var(--color-primary)] rounded"
                      >
                        Create an account
                      </Link>
                      <Link
                        to="/login"
                        onClick={() => setOpen(false)}
                        className="block px-4 py-2 btn btn-primary text-white rounded"
                      >
                        Log in
                      </Link>
                    </>
                  )}

                  {showLoginButton && (
                    <Link
                      to="/login"
                      onClick={() => setOpen(false)}
                      className="block px-4 py-2 btn btn-primary text-white rounded"
                    >
                      Login
                    </Link>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </header>
      ) : (
        // Non-auth pages show regular navbar fixed with high z-index
        <nav className="fixed top-0 left-0 right-0 z-50 border-b border-[#ccc] bg-white shadow-sm" aria-label="Main Navigation">
          <Navbar />
        </nav>
      )}

      <main id="main-content" role="main" className={`flex-grow ${isAuthPage ? "" : "p-0"} mt-[64px]`}>
        <Outlet />
      </main>

      {!isAuthPage && <Footer />}
    </div>
  );
};

export default Layout;
