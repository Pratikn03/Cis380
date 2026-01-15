import { BrowserRouter, Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Footer from "./components/Footer";
import CommandCenter from "./pages/CommandCenter";
import Chat from "./pages/Chat";
import DsaRag from "./pages/DsaRag";

export default function App() {
  return (
    <BrowserRouter basename={import.meta.env.BASE_URL}>
      <div className="flex min-h-screen flex-col md:flex-row">
        <Sidebar />
        <div className="flex flex-1 flex-col">
          <div className="flex-1">
            <Routes>
              <Route path="/" element={<CommandCenter />} />
              <Route path="/command-center" element={<CommandCenter />} />
              <Route path="/chat" element={<Chat />} />
              <Route path="/dsa-rag" element={<DsaRag />} />
            </Routes>
          </div>
          <Footer />
        </div>
      </div>
    </BrowserRouter>
  );
}
