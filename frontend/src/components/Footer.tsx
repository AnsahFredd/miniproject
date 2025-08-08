import React from "react";
import { FaTwitter, FaLinkedin, FaGithub } from "react-icons/fa";

const Footer = () => {
  return (
    <footer className="bg-[var(--color-primary)] text-white pt-12 pb-10 px-6 mt-8" role="contentinfo">
      <div className="max-w-7xl mx-auto grid gap-10 md:grid-cols-2 lg:grid-cols-4 text-center">
        {/* Brand */}
        <div>
          <h2 className="text-2xl font-bold">LawLens</h2>
          <p className="mt-3 text-sm text-white/90">
            Your AI-powered legal assistant for understanding, summarizing, and
            navigating legal documents with ease.
          </p>
        </div>

        {/* Navigation */}
        <nav aria-label="Footer Navigation">
          <h3 className="text-lg font-semibold mb-3">Navigation</h3>
          <ul className="space-y-2 text-sm text-white/90">
            <li>
              <a href="/dashboard" className="hover:text-[#0FA596] focus-visible:outline focus-visible:outline-offset-2 focus-visible:outline-white">
                Home
              </a>
            </li>
            <li>
              <a href="/document" className="hover:text-[#0FA596] focus-visible:outline focus-visible:outline-offset-2 focus-visible:outline-white">
                Dashboard
              </a>
            </li>
            <li>
              <a href="/search" className="hover:text-[#0FA596] focus-visible:outline focus-visible:outline-offset-2 focus-visible:outline-white">
                Search & QA
              </a>
            </li>
            <li>
              <a href="/settings" className="hover:text-[#0FA596] focus-visible:outline focus-visible:outline-offset-2 focus-visible:outline-white">
                Settings
              </a>
            </li>
          </ul>
        </nav>

        {/* Contact */}
        <div>
          <h3 className="text-lg font-semibold mb-3">Contact</h3>
          <ul className="space-y-2 text-sm text-white/90">
            <li>
              Email:{" "}
              <a href="mailto:support@lawlens.ai" className="hover:text-[#0FA596] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white">
                support@lawlens.ai
              </a>
            </li>
            <li>Phone: +233 (599) 288-539</li>
            <li>Kumasi, Ghana</li>
          </ul>
        </div>

        {/* Social */}
        <nav className="flex flex-col items-center lg:items-start " aria-label="Social Links">
          <h3 className="text-lg font-semibold mb-3">Follow Us</h3>
          <div className="flex space-x-4 text-xl text-white/90">
            <a href="#" aria-label="Twitter" className="hover:text-[#0FA596] focus-visible:outline focus-visible:outline-offset-2 focus-visible:outline-white"><FaTwitter /></a>
            <a href="https://www.linkedin.com/in/ansah-frederick-8a63b126b" aria-label="LinkedIn" className="hover:text-[#0FA596] focus-visible:outline focus-visible:outline-offset-2 focus-visible:outline-white"><FaLinkedin /></a>
            <a href="https://github.com/AnsahFredd/miniproject" aria-label="GitHub" target="_blank"   className="hover:text-[#0FA596] focus-visible:outline focus-visible:outline-offset-2 focus-visible:outline-white"><FaGithub /></a>
          </div>
        </nav>
      </div>

      <div className="mt-10 text-center text-sm text-white/80">
        &copy; {new Date().getFullYear()} LawLens. All rights reserved.
      </div>
    </footer>
  );
};

export default Footer;
