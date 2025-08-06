import React, { useState } from "react";
import backgroundImage from "../assets/images/background.png";
import landingimage1 from "../assets/images/landingimage1.png";
import landingimage2 from "../assets/images/landingimage2.png";
import landingimage3 from "../assets/images/landingimage3.png";
import { Link, Navigate } from "react-router-dom";

import { motion, AnimatePresence } from "framer-motion";

import { Search, HelpCircle, File, X, Menu } from "lucide-react";
import Button from "../components/ui/Button";
import { useAuth } from "../auth/AuthContext";

const LandingPage = () => {
  const [open, setOpen] = useState(false);

  const { token, loading } = useAuth();

  if (loading) return null;

  if (token) {
    return <Navigate to="/dashboard" replace />;
  }
  return (
    <div>
      {/* Hero Section */}
      <div
        className="w-screen h-[85vh] bg-no-repeat bg-cover bg-center relative"
        style={{ backgroundImage: `url(${backgroundImage})` }}
      >
        <div className="absolute inset-0 flex flex-col justify-center items-center text-white text-center px-4">
          <h1 className="text-3xl md:text-5xl font-bold mb-4 max-w-4xl">
            AI-Powered Legal Document Intelligence
          </h1>
          <p className="text-base md:text-lg leading-relaxed max-w-2xl">
            LawLens transforms how law firms, compliance officers, and
            researchers interact with legal documents. Our platform offers
            advanced AI capabilities for document parsing, clause
            identification, summarization, and question-answering, streamlining
            your workflow and enhancing decision-making.
          </p>
        </div>
      </div>

      {/* Features Section */}
      <section className="p-6 md:px-12 space-y-6 max-w-7xl mx-auto">
        <h2 className="text-3xl font-bold text-[#121417] text-center lg:text-left">
          Key Features
        </h2>
        <p className="text-[#121417] max-w-3xl mx-auto md:mx-0 text-center lg:text-left">
          Explore the core functionalities that make LawLens an indispensable
          tool for legal professionals.
        </p>

        <div className="flex flex-col lg:flex-row md:gap-8 gap-6 justify-center">
          {/* Card 1 */}
          <div className="border border-gray-300 rounded-lg p-6 flex flex-col items-center md:items-start text-center lg:text-left max-w-sm md:max-w-[320px] mx-auto">
            <File color="#4b4646cb" size={36} className="mb-4" />
            <h3 className="font-semibold text-xl mb-2 text-[#121417]">
              Document Parsing
            </h3>
            <p>
              Accurately extract key information from various legal document
              formats.
            </p>
          </div>

          {/* Card 2 */}
          <div className="border border-gray-300 rounded-lg p-6 flex flex-col items-center md:items-start text-center lg:text-left max-w-sm md:max-w-[320px] mx-auto">
            <Search color="#4b4646cb" size={36} className="mb-4" />
            <h3 className="font-semibold text-xl mb-2 text-[#121417]">
              Clause Identification
            </h3>
            <p>
              Quickly identify and analyze specific clauses within legal
              documents.
            </p>
          </div>

          {/* Card 3 */}
          <div className="border border-gray-300 rounded-lg p-6 flex flex-col items-center md:items-start text-center lg:text-left max-w-sm md:max-w-[320px] mx-auto">
            <div className="w-10 h-10 flex items-center justify-center border text-[#4b4646cb] rounded text-lg font-bold mb-4">
              B
            </div>
            <h3 className="font-semibold text-xl mb-2 text-[#121417]">
              Summarization
            </h3>
            <p>
              Generate concise summaries of lengthy legal documents, saving time
              and effort.
            </p>
          </div>

          {/* Card 4 */}
          <div className="border border-gray-300 rounded-lg p-6 flex flex-col items-center md:items-start text-center lg:text-left max-w-sm md:max-w-[320px] mx-auto">
            <HelpCircle color="#4b4646cb" size={36} className="mb-4" />
            <h3 className="font-semibold text-xl mb-2 text-[#121417]">
              Question-Answering
            </h3>
            <p>
              Get instant answers to your legal questions by querying documents
              directly.
            </p>
          </div>
        </div>
      </section>

      {/* Get Started Button */}
      <div className="flex justify-center items-center w-full mt-8 mb-8 px-4">
        <div className="w-full max-w-xs md:max-w-sm lg:max-w-md">
          <Link to="/signup">
            <Button
              label="Get Started"
              isLoading={false}
              otherStyles="bg-black text-white hover:bg-black/85 w-full"
            />
          </Link>
        </div>
      </div>

      {/* Solutions Section */}
      <section className="p-6 mt-11 space-y-6 max-w-7xl mx-auto">
        <h2 className="text-3xl font-bold text-[#121417] text-center lg:text-left">
          Solutions for Every Legal Professional
        </h2>

        <p className="text-[#121417] text-center lg:text-left max-w-3xl mx-auto md:mx-0">
          LawLens caters to the unique needs of different legal roles, providing
          tailored solutions for enhanced productivity and insights.
        </p>

        <div className="flex flex-col lg:flex-row md:space-x-8 space-y-8 md:space-y-0 mt-6 justify-center">
          {/* Card 1 */}
          <div className="flex flex-col items-center md:items-start text-center lg:text-left max-w-xs md:max-w-[280px] mx-auto">
            <img
              src={landingimage1}
              alt="For Law Firms"
              className="mb-4 w-full h-auto rounded-md shadow-sm"
            />
            <h3 className="font-semibold text-xl mb-2 text-[#121417]">
              For Law Firms
            </h3>
            <p className="text-gray-700">
              Streamline case preparation, contract review, and legal research
              with AI-powered tools.
            </p>
          </div>

          {/* Card 2 */}
          <div className="flex flex-col items-center md:items-start text-center lg:text-left max-w-xs md:max-w-[280px] mx-auto">
            <img
              src={landingimage2}
              alt="For Compliance Officers"
              className="mb-4 w-full h-auto rounded-md shadow-sm"
            />
            <h3 className="font-semibold text-xl mb-2 text-[#121417]">
              For Compliance Officers
            </h3>
            <p className="text-gray-700">
              Ensure regulatory compliance, manage risks, and monitor legal
              obligations effectively.
            </p>
          </div>

          {/* Card 3 */}
          <div className="flex flex-col items-center md:items-start text-center lg:text-left max-w-xs md:max-w-[280px] mx-auto">
            <img
              src={landingimage3}
              alt="For Researchers"
              className="mb-4 w-full h-auto rounded-md shadow-sm"
            />
            <h3 className="font-semibold text-xl mb-2 text-[#121417]">
              For Researchers
            </h3>
            <p className="text-gray-700">
              Accelerate legal research, analyze case law, and gain deeper
              insights into legal trends.
            </p>
          </div>
        </div>
      </section>

      {/* Call to Action Section */}
      <div className="p-6 flex flex-col items-center justify-center mt-11 space-y-6 max-w-7xl mx-auto">
        <h2 className="text-3xl font-bold text-[#121417] text-center lg:text-left max-w-4xl">
          Ready to Transform Your Legal Workflow?
        </h2>
        <p className="text-[#121417] text-center lg:text-left max-w-3xl mx-auto md:mx-0">
          Experience the power of LawLens firsthand. Request a demo today and
          discover how our AI-powered platform can revolutionize your legal
          document analysis.
        </p>
        <div className="flex justify-center items-center w-full mt-8 mb-8 px-4">
          <div className="w-full max-w-xs md:max-w-sm lg:max-w-md">
            <Button
              label="Request Demo"
              isLoading={false}
              onClick={() => ""}
              otherStyles="bg-blue-500 text-white hover:bg-black/85 w-full"
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;
