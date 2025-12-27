import { BrowserRouter, Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Footer from "./components/Footer";
import Home from "./pages/Home";
import CommandCenter from "./pages/CommandCenter";
import Architecture from "./pages/Architecture";
import Operations from "./pages/Operations";

export default function App() {
  return (
    <BrowserRouter basename={import.meta.env.BASE_URL}>
      <div className="flex min-h-screen flex-col md:flex-row">
        <Sidebar />
        <div className="flex flex-1 flex-col">
          <div className="flex-1">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/command" element={<CommandCenter />} />
              <Route path="/architecture" element={<Architecture />} />
              <Route path="/operations" element={<Operations />} />
            </Routes>
          </div>
          <Footer />
        </div>
      </div>
    </BrowserRouter>
  );
}
