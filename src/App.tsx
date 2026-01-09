import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  Sparkles,
  Zap,
  Download,
  Upload,
  Settings,
  Share2,
  BookOpen,
  Linkedin,
  Menu,
  X,
} from "lucide-react";

const App = () => {
  const [currentSection, setCurrentSection] = useState("home");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrollY, setScrollY] = useState(0);
  const [isLoaded, setIsLoaded] = useState(false);
  const [uploadedImage, setUploadedImage] = useState<File | null>(null);
  const [processedImageUrl, setProcessedImageUrl] = useState<string | null>(
    null
  );
  const [isProcessing, setIsProcessing] = useState(false);

  const [generatorSettings, setGeneratorSettings] = useState({
    quality: "low",
    palette: "math",
  });

  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => setIsLoaded(true), []);

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadedImage(file);
    setProcessedImageUrl(null);

    // Normalize values before sending
    const quality = generatorSettings.quality.toLowerCase();
    const palette = generatorSettings.palette.toLowerCase();

    const fd = new FormData();
    fd.append("file", file);
    fd.append("quality", quality);
    fd.append("palette", palette);

    console.log("Sending to backend:", {
      quality,
      palette,
      file: file.name,
    });

    try {
      setIsProcessing(true);
      const res = await fetch("/api/process", {
        method: "POST",
        body: fd,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail || `Server returned ${res.status}`);
      }

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      setProcessedImageUrl(url);
    } catch (err: any) {
      console.error("Processing failed:", err);
      alert("Processing failed: " + (err.message || err));
    } finally {
      setIsProcessing(false);
    }
  };

  const exportCanvas = () => {
    if (processedImageUrl) {
      const link = document.createElement("a");
      link.href = processedImageUrl;
      link.download = "symbol_art.png";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const shareArt = () => {
    alert("Sharing functionality is not implemented yet.");
  };

  const renderNav = useCallback(() => {
    const navItems = [
      {
        name: "Home",
        section: "home",
        icon: <Sparkles className="w-5 h-5" />,
      },
      {
        name: "About",
        section: "about",
        icon: <BookOpen className="w-5 h-5" />,
      },
    ];

    return (
      <nav
        className={`fixed top-0 z-50 w-full transition-all duration-300 ${
          scrollY > 50
            ? "bg-black/80 backdrop-blur-sm"
            : "bg-transparent"
        }`}
      >
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <a
            href="#"
            className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-500"
          >
            Symbol Art
          </a>
          <div className="hidden md:flex items-center space-x-8 text-gray-300 font-semibold">
            {navItems.map((item) => (
              <a
                key={item.section}
                href={`#${item.section}`}
                onClick={() => setCurrentSection(item.section)}
                className={`flex items-center gap-2 transition-colors hover:text-white ${
                  currentSection === item.section ? "text-white" : ""
                }`}
              >
                {item.icon}
                <span>{item.name}</span>
              </a>
            ))}
            <a
              href="#app"
              className="px-5 py-2 rounded-full font-bold transition-all bg-gradient-to-r from-cyan-400 to-purple-500 text-black hover:scale-105"
            >
              Launch App
            </a>
          </div>
          <button
            onClick={() => setMobileMenuOpen(true)}
            className="md:hidden text-white p-2"
          >
            <Menu className="w-6 h-6" />
          </button>
        </div>
        {mobileMenuOpen && (
          <div className="md:hidden fixed inset-0 bg-black/90 z-50 flex flex-col items-center justify-center space-y-8">
            <button
              onClick={() => setMobileMenuOpen(false)}
              className="absolute top-6 right-6 text-white p-2"
            >
              <X className="w-8 h-8" />
            </button>
            {navItems.map((item) => (
              <a
                key={item.section}
                href={`#${item.section}`}
                onClick={() => {
                  setCurrentSection(item.section);
                  setMobileMenuOpen(false);
                }}
                className={`text-3xl font-bold flex items-center gap-3 transition-colors ${
                  currentSection === item.section
                    ? "text-white"
                    : "text-gray-400"
                }`}
              >
                {item.icon}
                <span>{item.name}</span>
              </a>
            ))}
            <a
              href="#app"
              onClick={() => setMobileMenuOpen(false)}
              className="px-8 py-4 mt-8 rounded-full font-bold text-xl transition-all bg-gradient-to-r from-cyan-400 to-purple-500 text-black hover:scale-105"
            >
              Launch App
            </a>
          </div>
        )}
      </nav>
    );
  }, [scrollY, currentSection, mobileMenuOpen]);

  const renderSection = () => (
    <div className="space-y-12">
      {/* Home Section */}
      {currentSection === "home" && (
        <div
          id="home"
          className="pt-32 pb-24 text-center relative z-10 min-h-screen flex flex-col justify-center items-center"
        >
          <h1 className="text-5xl md:text-7xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-500 leading-tight drop-shadow-lg">
            Generate Mathematical Symbol Art
          </h1>
          <p className="mt-6 text-lg md:text-xl text-gray-300 max-w-3xl mx-auto drop-shadow-md">
            Transform any image into a breathtaking masterpiece of mathematical
            symbols, code, and cosmic patterns.
          </p>
          <div className="mt-10 flex flex-wrap justify-center gap-6">
            <a
              href="#app"
              className="inline-flex items-center px-8 py-4 font-bold text-black rounded-full transition-all bg-gradient-to-r from-cyan-400 to-purple-500 hover:scale-105 transform-gpu shadow-xl"
            >
              Start Creating{" "}
              <Zap className="ml-2 w-5 h-5 animate-pulse" />
            </a>
            <a
              href="#about"
              className="inline-flex items-center px-8 py-4 font-bold text-white border border-white/20 rounded-full transition-all backdrop-blur-sm hover:bg-white/10 transform-gpu hover:scale-105"
            >
              Learn More
            </a>
          </div>

          {/* Canvas */}
          <div className="w-full mt-20 p-8 bg-white/5 rounded-3xl shadow-lg border border-white/10 backdrop-blur-sm">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-3xl font-bold flex items-center gap-3">
                <Zap className="w-8 h-8 text-yellow-400 animate-pulse" />
                Symbol Art Canvas
              </h2>
              <div className="flex gap-3">
                <button
                  onClick={exportCanvas}
                  className="p-3 rounded-full text-white bg-white/10 transition-colors hover:bg-white/20"
                >
                  <Download className="w-5 h-5" />
                </button>
                <button
                  onClick={shareArt}
                  className="p-3 rounded-full text-white bg-white/10 transition-colors hover:bg-white/20"
                >
                  <Share2 className="w-5 h-5" />
                </button>
              </div>
            </div>

            <div className="relative group">
              {isProcessing ? (
                <div className="w-full h-96 bg-gray-800 rounded-2xl flex items-center justify-center">
                  <p className="text-gray-200">Processing...</p>
                </div>
              ) : processedImageUrl ? (
                <div className="w-full h-96 bg-gray-800 rounded-2xl flex items-center justify-center">
                  <img
                    src={processedImageUrl}
                    alt="Processed"
                    className="max-h-96 max-w-full object-contain rounded-lg"
                  />
                </div>
              ) : uploadedImage ? (
                <div className="w-full h-96 bg-gray-800 rounded-2xl flex items-center justify-center">
                  <p className="text-gray-400">
                    Uploaded. Ready to process.
                  </p>
                </div>
              ) : (
                <div className="w-full h-96 bg-gray-800 rounded-2xl flex items-center justify-center">
                  <p className="text-gray-400">
                    Upload a face image to get started.
                  </p>
                </div>
              )}
            </div>

            {/* Controls */}
            <div className="w-full mt-10 p-8 bg-white/5 rounded-3xl shadow-lg border border-white/10 backdrop-blur-sm">
              <div className="grid lg:grid-cols-2 gap-8">
                {/* Upload */}
                <div>
                  <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                    <Upload className="w-5 h-5" /> Image Upload
                  </h3>
                  <label className="flex flex-col items-center justify-center p-8 border-2 border-dashed border-cyan-400 rounded-lg cursor-pointer bg-white/5 transition-all hover:bg-white/10">
                    <input
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={handleImageUpload}
                    />
                    <Upload className="w-10 h-10 text-cyan-400 mb-2" />
                    <p className="text-gray-200 font-semibold text-center">
                      Drag & Drop or Click to Upload
                    </p>
                    <p className="text-gray-400 text-sm mt-1">
                      PNG, JPG, JPEG up to 10MB
                    </p>
                  </label>
                </div>

                {/* Quality Controls */}
                <div>
                  <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    <Settings className="w-5 h-5" /> Generation Controls
                  </h3>
                  <div className="mt-2 flex items-center gap-4">
                    <button
                      onClick={() =>
                        setGeneratorSettings((prev) => ({
                          ...prev,
                          quality: "low",
                        }))
                      }
                      className={`px-4 py-2 rounded-full font-bold transition-all ${
                        generatorSettings.quality === "low"
                          ? "bg-gradient-to-r from-cyan-400 to-purple-500 text-black"
                          : "bg-gray-700 text-gray-300 hover:bg-gray-600"
                      }`}
                    >
                      Low
                    </button>
                    <button
                      onClick={() =>
                        setGeneratorSettings((prev) => ({
                          ...prev,
                          quality: "medium",
                        }))
                      }
                      className={`px-4 py-2 rounded-full font-bold transition-all ${
                        generatorSettings.quality === "medium"
                          ? "bg-gradient-to-r from-cyan-400 to-purple-500 text-black"
                          : "bg-gray-700 text-gray-300 hover:bg-gray-600"
                      }`}
                    >
                      Medium
                    </button>
                    <button
                      onClick={() =>
                        setGeneratorSettings((prev) => ({
                          ...prev,
                          quality: "high",
                        }))
                      }
                      className={`px-4 py-2 rounded-full font-bold transition-all ${
                        generatorSettings.quality === "high"
                          ? "bg-gradient-to-r from-cyan-400 to-purple-500 text-black"
                          : "bg-gray-700 text-gray-300 hover:bg-gray-600"
                      }`}
                    >
                      High
                    </button>
                  </div>

                  <div className="mt-6">
                    <p className="text-sm font-semibold text-gray-300">
                      Palette
                    </p>
                    <select
                      value={generatorSettings.palette}
                      onChange={(e) =>
                        setGeneratorSettings((prev) => ({
                          ...prev,
                          palette: e.target.value.toLowerCase(),
                        }))
                      }
                      className="px-4 py-2 rounded-lg bg-gray-700 text-white border-none focus:ring-2 focus:ring-cyan-400 mt-2"
                    >
                      <option value="math">Mathematical</option>
                      <option value="ascii">ASCII</option>
                      <option value="greek">Greek</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* About Section */}
      {currentSection === "about" && (
        <div
          id="about"
          className="pt-32 pb-24 min-h-screen text-center space-y-12"
        >
          <h2 className="text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-500">
            About Symbol Art
          </h2>
          <p className="text-lg md:text-xl text-gray-300 max-w-4xl mx-auto">
            Symbol Art transforms your photos into intricate mathematical symbol
            masterpieces, blending technology and aesthetics.
          </p>

          <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-center">
            <div>
              <img
                src="https://via.placeholder.com/300x300?text=Low"
                alt="Low Output"
                className="mx-auto rounded-lg"
              />
            </div>
            <div>
              <img
                src="https://via.placeholder.com/300x300?text=Medium"
                alt="Medium Output"
                className="mx-auto rounded-lg"
              />
            </div>
            <div>
              <img
                src="https://via.placeholder.com/300x300?text=High"
                alt="High Output"
                className="mx-auto rounded-lg"
              />
            </div>
            <div>
              <img
                src="https://via.placeholder.com/300x300?text=Extra"
                alt="Extra Output"
                className="mx-auto rounded-lg"
              />
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="w-full py-8 bg-black/90 flex flex-col items-center text-gray-400">
        <div className="flex justify-center gap-6 mt-4">
          <a
            href="https://www.linkedin.com/in/yourprofile"
            aria-label="LinkedIn"
            className="hover:text-white transition-colors"
          >
            <Linkedin className="w-6 h-6" />
          </a>
        </div>
        <p className="mt-6 text-sm">
          &copy; 2025 Symbol Art. All Rights Reserved.
        </p>
      </footer>
    </div>
  );

  return (
    <div className="bg-black text-white font-sans">
      {renderNav()}
      {renderSection()}
    </div>
  );
};

export default App;
