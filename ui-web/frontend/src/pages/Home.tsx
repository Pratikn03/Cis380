/**
 * ==============================================================================
 * HOME PAGE - Main Landing Page for Portfolio Website
 * ==============================================================================
 * Author: Pratik Niroula
 * Project: Universal Anomaly Intelligence System (UAIS)
 *
 * WHAT THIS FILE DOES:
 * --------------------
 * This is the main landing page of the portfolio website. It displays:
 * 1. Hero section with name and introduction
 * 2. Statistics showing project achievements
 * 3. Core capabilities (the 6 ML modules)
 * 4. Technology stack used in the project
 * 5. Call-to-action to view the live demo
 *
 * REACT CONCEPTS USED:
 * --------------------
 * - Functional Component: `export default function Home()`
 * - JSX: HTML-like syntax in JavaScript
 * - Props: Not used here (static content)
 * - Array.map(): To render lists of items (stats, features, tech stack)
 * - Link: React Router component for navigation without page reload
 *
 * TAILWIND CSS:
 * -------------
 * This file uses Tailwind CSS utility classes for styling:
 * - bg-slate-900: Dark background color
 * - text-emerald-400: Green text color
 * - grid md:grid-cols-3: 3-column grid on medium+ screens
 * - hover:bg-emerald-400: Color change on mouse hover
 *
 * FILE STRUCTURE:
 * ---------------
 *   Home.tsx (this file)
 *       │
 *       ├── Hero Section (name, title, description, buttons)
 *       ├── Stats Section (Images Processed, ML Models, etc.)
 *       ├── Features Section (Fraud, Vision, Cyber, NLP, Behavior, Fusion)
 *       ├── Tech Stack Section (Python, React, PyTorch, etc.)
 *       └── CTA Section (Launch Command Center button)
 * ==============================================================================
 */

import { Link } from "react-router-dom"; // React Router for navigation

/**
 * Home Component
 *
 * The main landing page of the portfolio website.
 * This is a "functional component" - a JavaScript function that returns JSX.
 *
 * @returns JSX.Element - The rendered HTML-like content
 */
export default function Home() {
  return (
    // Main container - full screen height with gradient background
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-20 pb-32 px-6">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-emerald-900/20 via-transparent to-transparent"></div>
        <div className="relative z-10 max-w-5xl mx-auto text-center">
          <p className="text-emerald-400 font-medium tracking-wide uppercase text-sm">
            Full-Stack Developer & ML Engineer
          </p>
          <h1 className="mt-6 text-5xl md:text-7xl font-bold bg-gradient-to-r from-white via-emerald-100 to-emerald-300 bg-clip-text text-transparent leading-tight">
            Pratik Niroula
          </h1>
          <p className="mt-8 text-xl text-slate-300 max-w-2xl mx-auto leading-relaxed">
            Building intelligent systems that detect anomalies, prevent fraud, and secure digital infrastructure through advanced machine learning.
          </p>
          <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/command-center"
              className="px-8 py-4 bg-emerald-500 hover:bg-emerald-400 text-slate-900 font-semibold rounded-xl transition-all shadow-lg shadow-emerald-500/25 hover:shadow-emerald-400/40"
            >
              Live Demo
            </Link>
            <a
              href="https://github.com/Pratikn03"
              target="_blank"
              rel="noopener noreferrer"
              className="px-8 py-4 border border-slate-600 hover:border-emerald-400 text-slate-200 font-semibold rounded-xl transition-all hover:text-emerald-300"
            >
              GitHub Profile
            </a>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 px-6 bg-slate-800/50">
        <div className="max-w-6xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8">
          {[
            { value: "154K+", label: "Images Processed" },
            { value: "6", label: "ML Models" },
            { value: "99.2%", label: "Detection Accuracy" },
            { value: "5+", label: "Integrated APIs" },
          ].map((stat, i) => (
            <div key={i} className="text-center">
              <p className="text-4xl font-bold text-emerald-400">{stat.value}</p>
              <p className="mt-2 text-slate-400">{stat.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-white text-center mb-4">Core Capabilities</h2>
          <p className="text-slate-400 text-center mb-12 max-w-2xl mx-auto">
            A unified platform combining multiple detection engines for comprehensive security analysis
          </p>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                title: "Fraud Detection",
                desc: "Real-time transaction analysis using ensemble methods and anomaly detection algorithms",
                icon: "🛡️",
              },
              {
                title: "Vision Analysis",
                desc: "Image classification for detecting manipulated media and synthetic content",
                icon: "👁️",
              },
              {
                title: "Cyber Security",
                desc: "Network intrusion detection with pattern recognition and behavioral analysis",
                icon: "🔐",
              },
              {
                title: "NLP Processing",
                desc: "Text classification for sentiment analysis and threat detection in communications",
                icon: "📝",
              },
              {
                title: "Behavior Analytics",
                desc: "User behavior modeling to identify insider threats and account compromise",
                icon: "📊",
              },
              {
                title: "Model Fusion",
                desc: "Multi-modal ensemble combining all detection engines for superior accuracy",
                icon: "🔗",
              },
            ].map((feature, i) => (
              <div
                key={i}
                className="p-6 bg-slate-800/60 rounded-2xl border border-slate-700 hover:border-emerald-500/50 transition-all group"
              >
                <span className="text-4xl">{feature.icon}</span>
                <h3 className="mt-4 text-xl font-semibold text-white group-hover:text-emerald-300 transition-colors">
                  {feature.title}
                </h3>
                <p className="mt-2 text-slate-400">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Tech Stack */}
      <section className="py-20 px-6 bg-slate-800/30">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-white text-center mb-12">Technology Stack</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {[
              { name: "Python", category: "Backend" },
              { name: "FastAPI", category: "API" },
              { name: "React", category: "Frontend" },
              { name: "TypeScript", category: "Frontend" },
              { name: "PyTorch", category: "ML" },
              { name: "scikit-learn", category: "ML" },
              { name: "PostgreSQL", category: "Database" },
              { name: "Docker", category: "DevOps" },
            ].map((tech, i) => (
              <div
                key={i}
                className="p-4 bg-slate-800 rounded-xl text-center border border-slate-700"
              >
                <p className="font-semibold text-white">{tech.name}</p>
                <p className="text-sm text-emerald-400">{tech.category}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-4">Explore the Platform</h2>
          <p className="text-slate-400 mb-8">
            See the live demo of our anomaly detection command center
          </p>
          <Link
            to="/command-center"
            className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-900 font-semibold rounded-xl hover:from-emerald-400 hover:to-teal-400 transition-all shadow-lg"
          >
            Launch Command Center
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </Link>
        </div>
      </section>
    </main>
  );
}
