import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import Home from "./pages/Home";
import Saved from "./pages/Saved";
import Upload from "./pages/Upload";
import Closet from "./pages/Closet";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/saved" element={<Saved />} />
        <Route path="/upload" element={<Upload />} />
        <Route path="/closet" element={<Closet />} />
      </Routes>
    </BrowserRouter>
  );
}