import React from "react";
import { FaTwitter, FaLinkedin, FaGithub } from "react-icons/fa";

const Footer = () => {
  return (
    <footer className="bg-gray-900 text-gray-300 py-10 px-6">
      <div className="max-w-7xl mx-auto flex flex-col items-center text-center gap-10 md:flex-col md:items-center md:text-center lg:grid lg:grid-cols-4 lg:items-start lg:text-left">
        {/* Brand */}
        <div>
          <h2 className="text-2xl font-bold text-white">LawLens</h2>
          <p className="mt-2 text-sm leading-relaxed">
            Your AI-powered legal assistant for understanding, summarizing, and
            navigating legal documents with ease.
          </p>
        </div>

        {/* Navigation */}
        <div>
          <h3 className="text-lg font-semibold text-white mb-3">Navigation</h3>
          <ul className="space-y-2 text-sm">
            <li>
              <a href="/" className="hover:text-white">
                Home
              </a>
            </li>
            <li>
              <a href="/dashboard" className="hover:text-white">
                Dashboard
              </a>
            </li>
            <li>
              <a href="/search" className="hover:text-white">
                Search & QA
              </a>
            </li>
            <li>
              <a href="/settings" className="hover:text-white">
                Settings
              </a>
            </li>
          </ul>
        </div>

        {/* Contact */}
        <div>
          <h3 className="text-lg font-semibold text-white mb-3">Contact</h3>
          <ul className="space-y-2 text-sm">
            <li>
              Email:{" "}
              <a href="mailto:support@lawlens.ai" className="hover:text-white">
                support@lawlens.ai
              </a>
            </li>
            <li>Phone: +233 (599) 288-539</li>
            <li>Kumasi, Ghana</li>
          </ul>
        </div>

        {/* Social */}
        <div className="flex flex-col items-center justify-center">
          <h3 className="text-lg font-semibold text-white mb-3">Follow Us</h3>
          <div className="flex justify-center space-x-4 text-xl">
            <a href="#" className="hover:text-white">
              <FaTwitter />
            </a>
            <a href="#" className="hover:text-white">
              <FaLinkedin />
            </a>
            <a href="#" className="hover:text-white">
              <FaGithub />
            </a>
          </div>
        </div>
      </div>

      <div className="mt-10 text-center text-sm text-gray-500">
        &copy; {new Date().getFullYear()} LawLens. All rights reserved.
      </div>
    </footer>
  );
};

export default Footer;
