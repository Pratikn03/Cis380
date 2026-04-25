import { BrowserRouter, Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Footer from "./components/Footer";
import CommandCenter from "./pages/CommandCenter";
import Chat from "./pages/Chat";
import Agent from "./pages/Agent";
import Fraud from "./pages/Fraud";
import Cyber from "./pages/Cyber";
import Brand from "./pages/Brand";
import Behavior from "./pages/Behavior";
import Recommender from "./pages/Recommender";
import RAG from "./pages/RAG";
import Admin from "./pages/Admin";
import Health from "./pages/Health";
import Settings from "./pages/Settings";

const resolveBase = () => {
  const baseUrl = import.meta.env.BASE_URL || "/";
  if (baseUrl.startsWith("/")) {
    return baseUrl;
  }
  if (typeof window === "undefined") {
    return "/";
  }
  return new URL(baseUrl, window.location.href).pathname;
};

export default function App() {
  return (
    <BrowserRouter basename={resolveBase()}>
      <div className="flex min-h-screen flex-col md:flex-row">
        <Sidebar />
        <div className="flex flex-1 flex-col">
          <div className="flex-1">
            <Routes>
              <Route path="/" element={<CommandCenter />} />
              <Route path="/command-center" element={<CommandCenter />} />
              <Route path="/agent" element={<Agent />} />
              <Route path="/fraud" element={<Fraud />} />
              <Route path="/cyber" element={<Cyber />} />
              <Route path="/brand" element={<Brand />} />
              <Route path="/behavior" element={<Behavior />} />
              <Route path="/recommender" element={<Recommender />} />
              <Route path="/rag" element={<RAG />} />
              <Route path="/admin" element={<Admin />} />
              <Route path="/health" element={<Health />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/chat" element={<Chat />} />
            </Routes>
          </div>
          <Footer />
        </div>
      </div>
    </BrowserRouter>
  );
}
