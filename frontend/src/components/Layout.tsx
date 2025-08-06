import { Outlet, useLocation, Link } from "react-router-dom";
import Navbar from "./Navbar";
import Footer from "./Footer";
import { useAuth } from "../auth/AuthContext";
import { useState } from "react";
import { Menu, X, Search } from "lucide-react";
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
      {isAuthPage ? (
        <header className="fixed top-0 left-0 right-0 z-50 border-b border-gray-200 shadow-sm bg-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <nav className="flex items-center justify-between h-18">
              {/* Logo + Title */}
              <div className="flex items-center space-x-2">
                <h1 className="text-xl font-bold text-gray-800">LawLens</h1>
              </div>

              {/* Desktop Buttons */}
              {showSignupLogin && (
                <div className="hidden lg:flex items-center space-x-4">
                  <Link
                    to="/signup"
                    className="bg-black text-white px-4 py-2 rounded text-sm"
                  >
                    Create an account
                  </Link>
                  <Link
                    to="/login"
                    className="bg-blue-600 text-white px-4 py-2 rounded text-sm"
                  >
                    Log in
                  </Link>
                </div>
              )}

              {showLoginButton && (
                <div className="hidden lg:flex">
                  <Link
                    to="/login"
                    className="bg-[#4080BF] text-white px-4 py-2 rounded text-sm"
                  >
                    Login
                  </Link>
                </div>
              )}

              {/* Mobile Hamburger */}
              <div className="lg:hidden">
                <button
                  onClick={() => setOpen(!open)}
                  className="text-gray-800"
                >
                  {open ? <X size={24} /> : <Menu size={24} />}
                </button>
              </div>
            </nav>

            {/* Mobile Dropdown */}
            <AnimatePresence>
              {open && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.3 }}
                  className="lg:hidden mt-2 space-y-2 pb-4"
                >
                  {showSignupLogin && (
                    <>
                      <Link
                        to="/signup"
                        onClick={() => setOpen(false)}
                        className="block px-4 py-2 bg-black text-white rounded"
                      >
                        Create an account
                      </Link>
                      <Link
                        to="/login"
                        onClick={() => setOpen(false)}
                        className="block px-4 py-2 bg-blue-600 text-white rounded"
                      >
                        Log in
                      </Link>
                    </>
                  )}

                  {showLoginButton && (
                    <Link
                      to="/login"
                      onClick={() => setOpen(false)}
                      className="block px-4 py-2 bg-[#4080BF] text-white rounded"
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
        // Non-auth pages show regular navbar fixed below the header space
        <nav className="fixed top-0 left-0 right-0 z-50 border-b border-[#ccc] bg-white shadow-sm">
          <Navbar />
        </nav>
      )}

      <main className={`flex-grow ${isAuthPage ? "" : "p-6"} mt-[72px]`}>
        <Outlet />
      </main>

      {!isAuthPage && <Footer />}
    </div>
  );
};

export default Layout;
