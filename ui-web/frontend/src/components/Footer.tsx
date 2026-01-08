export default function Footer() {
  return (
    <footer className="bg-slate-900 border-t border-slate-700 px-6 py-6">
      <div className="max-w-6xl mx-auto flex flex-wrap items-center justify-between gap-4 text-sm text-slate-400">
        <p>© 2026 Pratik Narwadkar. All rights reserved.</p>
        <div className="flex items-center gap-4">
          <a
            href="https://github.com/Pratikn03"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-emerald-400 transition-colors"
          >
            GitHub
          </a>
          <a
            href="https://linkedin.com/in/pratiknarwadkar"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-emerald-400 transition-colors"
          >
            LinkedIn
          </a>
        </div>
      </div>
    </footer>
  );
}
