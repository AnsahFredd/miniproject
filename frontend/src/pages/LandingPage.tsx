import React, { useState } from "react";
import backgroundImage from "../assets/images/background.png";
import landingimage1 from "../assets/images/landingimage1.png";
import landingimage2 from "../assets/images/landingimage2.png";
import landingimage3 from "../assets/images/landingimage3.png";
import { Link, Navigate, useNavigate } from "react-router-dom";


const API = import.meta.env.VITE_API_BASE_URL;


import { Search, HelpCircle, File, X, Menu } from 'lucide-react';
import Button from "../components/ui/Button";
import { useAuth } from "../auth/AuthContext";

const LandingPage = () => {
  const [open, setOpen] = useState(false);

  const { token, loading } = useAuth();

  if (loading) return null;

  if (token) {
    return <Navigate to="/dashboard" replace />;
  }

  const navigate = useNavigate();


  const handleDemo = async () => {
    const res = await fetch(`${API}/demo`);
    const data = await res.json();
    navigate("/demo", { state: { demoData: data } });
  };


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
        <h2 className="text-3xl font-bold text-[var(--color-primary)] text-center lg:text-left">
          Key Features
        </h2>
        <p className="text-[var(--color-secondary)] max-w-3xl mx-auto md:mx-0 text-center lg:text-left">
          Explore the core functionalities that make LawLens an indispensable
          tool for legal professionals.
        </p>

        <div className="flex flex-col lg:flex-row md:gap-8 gap-6 justify-center">
          {/* Card 1 */}
          <div className="card p-6 flex flex-col items-center md:items-start text-center lg:text-left max-w-sm md:max-w-[320px] mx-auto">
            <File color="currentColor" className="text-[var(--color-primary)] mb-4" size={36} />
            <h3 className="font-semibold text-xl mb-2 text-[var(--color-primary)]">
              Document Parsing
            </h3>
            <p className="text-[var(--color-secondary)]">
              Accurately extract key information from various legal document
              formats.
            </p>
          </div>

          {/* Card 2 */}
          <div className="card p-6 flex flex-col items-center md:items-start text-center lg:text-left max-w-sm md:max-w-[320px] mx-auto">
            <Search color="currentColor" className="text-[var(--color-primary)] mb-4" size={36} />
            <h3 className="font-semibold text-xl mb-2 text-[var(--color-primary)]">
              Clause Identification
            </h3>
            <p className="text-[var(--color-secondary)]">
              Quickly identify and analyze specific clauses within legal
              documents.
            </p>
          </div>

          {/* Card 3 */}
          <div className="card p-6 flex flex-col items-center md:items-start text-center lg:text-left max-w-sm md:max-w-[320px] mx-auto">
            <div className="w-10 h-10 flex items-center justify-center border text-[var(--color-primary)] rounded text-lg font-bold mb-4">
              B
            </div>
            <h3 className="font-semibold text-xl mb-2 text-[var(--color-primary)]">
              Summarization
            </h3>
            <p className="text-[var(--color-secondary)]">
              Generate concise summaries of lengthy legal documents, saving time
              and effort.
            </p>
          </div>

          {/* Card 4 */}
          <div className="card p-6 flex flex-col items-center md:items-start text-center lg:text-left max-w-sm md:max-w-[320px] mx-auto">
            <HelpCircle color="currentColor" className="text-[var(--color-primary)] mb-4" size={36} />
            <h3 className="font-semibold text-xl mb-2 text-[var(--color-primary)]">
              Question-Answering
            </h3>
            <p className="text-[var(--color-secondary)]">
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
              otherStyles="btn btn-primary w-full"
            />
          </Link>
        </div>
      </div>

      {/* Solutions Section */}
      <section className="p-6 mt-11 space-y-6 max-w-7xl mx-auto">
        <h2 className="text-3xl font-bold text-[var(--color-primary)] text-center lg:text-left">
          Solutions for Every Legal Professional
        </h2>

        <p className="text-[var(--color-secondary)] text-center lg:text-left max-w-3xl mx-auto md:mx-0">
          LawLens caters to the unique needs of different legal roles, providing
          tailored solutions for enhanced productivity and insights.
        </p>

        <div className="flex flex-col lg:flex-row md:space-x-8 space-y-8 md:space-y-0 mt-6 justify-center">
          {/* Card 1 */}
          <div className="flex flex-col items-center md:items-start text-center lg:text-left max-w-xs md:max-w-[280px] mx-auto card p-4">
            <img
              src={landingimage1 || "/placeholder.svg"}
              alt="For Law Firms"
              className="mb-4 w-full h-auto rounded-md shadow-sm"
            />
            <h3 className="font-semibold text-xl mb-2 text-[var(--color-primary)]">
              For Law Firms
            </h3>
            <p className="text-[var(--color-secondary)]">
              Streamline case preparation, contract review, and legal research
              with AI-powered tools.
            </p>
          </div>

          {/* Card 2 */}
          <div className="flex flex-col items-center md:items-start text-center lg:text-left max-w-xs md:max-w-[280px] mx-auto card p-4">
            <img
              src={landingimage2 || "/placeholder.svg"}
              alt="For Compliance Officers"
              className="mb-4 w-full h-auto rounded-md shadow-sm"
            />
            <h3 className="font-semibold text-xl mb-2 text-[var(--color-primary)]">
              For Compliance Officers
            </h3>
            <p className="text-[var(--color-secondary)]">
              Ensure regulatory compliance, manage risks, and monitor legal
              obligations effectively.
            </p>
          </div>

          {/* Card 3 */}
          <div className="flex flex-col items-center md:items-start text-center lg:text-left max-w-xs md:max-w-[280px] mx-auto card p-4">
            <img
              src={landingimage3 || "/placeholder.svg"}
              alt="For Researchers"
              className="mb-4 w-full h-auto rounded-md shadow-sm"
            />
            <h3 className="font-semibold text-xl mb-2 text-[var(--color-primary)]">
              For Researchers
            </h3>
            <p className="text-[var(--color-secondary)]">
              Accelerate legal research, analyze case law, and gain deeper
              insights into legal trends.
            </p>
          </div>
        </div>
      </section>

      {/* Call to Action Section */}
      <div className="p-6 flex flex-col items-center justify-center mt-11 space-y-6 max-w-7xl mx-auto">
        <h2 className="text-3xl font-bold text-[var(--color-primary)] text-center lg:text-left max-w-4xl">
          Ready to Transform Your Legal Workflow?
        </h2>
        <p className="text-[var(--color-secondary)] text-center lg:text-left max-w-3xl mx-auto md:mx-0">
          Experience the power of LawLens firsthand. Request a demo today and
          discover how our AI-powered platform can revolutionize your legal
          document analysis.
        </p>
        <div className="flex justify-center items-center w-full mt-8 mb-8 px-4">
          <div className="w-full max-w-xs md:max-w-sm lg:max-w-md">
            <Button
              label="Request Demo"
              isLoading={false}
              onClick={handleDemo}
              otherStyles="btn btn-secondary w-full"
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;
