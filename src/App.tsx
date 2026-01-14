import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  Download,
  Upload,
  Share2,
  BookOpen,
  Linkedin,
  Menu,
  X,
  Feather,
  Crown,
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
      const res = await fetch("/process", {
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
        icon: <Feather className="w-4 h-4" />,
      },
      {
        name: "About",
        section: "about",
        icon: <BookOpen className="w-4 h-4" />,
      },
    ];

    return (
      <nav
        className={`fixed top-0 z-50 w-full transition-all duration-700 ${scrollY > 50
          ? "bg-midnight/90 backdrop-blur-md border-b border-gold-accent/20"
          : "bg-transparent"
          }`}
      >
        <div className="max-w-7xl mx-auto px-6 py-6 flex items-center justify-between">
          <a
            href="#"
            className="text-3xl font-display text-gold-accent tracking-widest hover:opacity-80 transition-opacity"
          >
            Symbol Art
          </a>
          <div className="hidden md:flex items-center space-x-12">
            {navItems.map((item) => (
              <a
                key={item.section}
                href={`#${item.section}`}
                onClick={() => setCurrentSection(item.section)}
                className={`flex items-center gap-2 font-body text-lg tracking-wide transition-all duration-300 hover:text-gold-accent ${currentSection === item.section ? "text-gold-accent" : "text-gray-400"
                  }`}
              >
                {item.icon}
                <span className="uppercase text-sm">{item.name}</span>
              </a>
            ))}
            <a
              href="#app"
              className="px-8 py-2 border border-gold-accent/50 text-gold-accent font-display tracking-widest hover:bg-gold-accent hover:text-midnight transition-all duration-500 rounded-sm"
            >
              CREATE
            </a>
          </div>
          <button
            onClick={() => setMobileMenuOpen(true)}
            className="md:hidden text-gold-accent p-2"
          >
            <Menu className="w-6 h-6" />
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden fixed inset-0 bg-midnight z-50 flex flex-col items-center justify-center space-y-8 animate-fade-in">
            <button
              onClick={() => setMobileMenuOpen(false)}
              className="absolute top-6 right-6 text-gold-accent p-2"
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
                className={`text-4xl font-display text-gold-accent hover:scale-110 transition-transform`}
              >
                {item.name}
              </a>
            ))}
          </div>
        )}
      </nav>
    );
  }, [scrollY, currentSection, mobileMenuOpen]);

  // Reusable ornate button component for quality selection
  const QualityButton = ({ value, label }: { value: string, label: string }) => (
    <button
      onClick={() =>
        setGeneratorSettings((prev) => ({
          ...prev,
          quality: value,
        }))
      }
      className={`relative group px-6 py-3 min-w-[120px] transition-all duration-500 overflow-hidden ${generatorSettings.quality === value
        ? "text-midnight"
        : "text-gold-accent"
        }`}
    >
      <div className={`absolute inset-0 border border-gold-accent/30 transition-all duration-500 ${generatorSettings.quality === value ? "bg-gold-accent" : "bg-transparent group-hover:bg-gold-accent/10"
        }`} />
      <span className={`relative z-10 font-display text-lg tracking-wider ${generatorSettings.quality === value ? "font-bold" : ""
        }`}>
        {label}
      </span>
    </button>
  );

  const renderSection = () => (
    <div className="space-y-24 pb-24">
      {/* Home Section */}
      {currentSection === "home" && (
        <div
          id="home"
          className="pt-40 min-h-screen flex flex-col items-center relative"
        >
          {/* Decorative background elements */}
          <div className="absolute top-1/4 left-10 w-64 h-64 bg-purple-900/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute bottom-1/4 right-10 w-96 h-96 bg-gold-accent/5 rounded-full blur-3xl pointer-events-none" />

          <div className="text-center space-y-8 z-10 px-4 max-w-5xl mx-auto">
            <h1 className="text-6xl md:text-8xl font-display text-gold-accent leading-tight drop-shadow-2xl animate-fade-in-up">
              The Art of <br />
              <span className="font-script text-7xl md:text-9xl text-white/90">Equations</span>
            </h1>
            <p className="mt-8 text-xl md:text-2xl font-body italic text-gray-300 max-w-2xl mx-auto leading-relaxed">
              "Logic and beauty are two sides of the same coin. Let your images speak the language of the universe."
            </p>

            <div className="mt-16 flex justify-center">
              <a
                href="#app"
                className="group relative px-12 py-4 overflow-hidden"
              >
                <div className="absolute inset-0 w-full h-full border border-gold-accent/50 rotate-1 transition-transform group-hover:rotate-0" />
                <div className="absolute inset-0 w-full h-full border border-gold-accent/50 -rotate-1 transition-transform group-hover:rotate-0" />
                <span className="relative font-display text-xl text-gold-accent tracking-[0.2em] group-hover:text-white transition-colors">
                  BEGIN JOURNEY
                </span>
              </a>
            </div>
          </div>

          {/* Canvas & Controls Section */}
          <div id="app" className="w-[90%] max-w-6xl mt-32 p-1 bg-gradient-to-br from-gold-accent/20 via-transparent to-gold-accent/20 rounded-sm">
            <div className="w-full bg-midnight/95 p-8 md:p-12 relative overflow-hidden backdrop-blur-xl border border-white/5">

              <div className="flex flex-col md:flex-row items-center justify-between mb-12 border-b border-white/5 pb-8">
                <h2 className="text-4xl font-display text-white flex items-center gap-4">
                  <Crown className="w-8 h-8 text-gold-accent" />
                  Your Canvas
                </h2>
                <div className="flex gap-4 mt-4 md:mt-0">
                  <button
                    onClick={exportCanvas}
                    className="p-3 text-gold-accent hover:text-white transition-colors"
                    title="Download Masterpiece"
                  >
                    <Download className="w-6 h-6" />
                  </button>
                  <button
                    onClick={shareArt}
                    className="p-3 text-gold-accent hover:text-white transition-colors"
                  >
                    <Share2 className="w-6 h-6" />
                  </button>
                </div>
              </div>

              <div className="grid lg:grid-cols-2 gap-16">
                {/* The Frame / Display */}
                <div className="relative group">
                  <div className="absolute -inset-1 bg-gradient-to-r from-gold-accent/30 to-purple-900/30 rounded-lg blur opacity-50 group-hover:opacity-100 transition duration-1000"></div>
                  <div className="relative w-full h-[500px] bg-black/40 border border-white/10 flex items-center justify-center overflow-hidden">
                    {isProcessing ? (
                      <div className="text-center space-y-4">
                        <div className="w-16 h-16 border-t-2 border-gold-accent rounded-full animate-spin mx-auto" />
                        <p className="font-display text-xl text-gold-accent animate-pulse">Weaving Symbols...</p>
                      </div>
                    ) : processedImageUrl ? (
                      <img
                        src={processedImageUrl}
                        alt="Processed Art"
                        className="w-full h-full object-contain"
                      />
                    ) : (
                      <div className="text-center p-8 border border-dashed border-white/10 rounded-lg m-8">
                        <Feather className="w-12 h-12 text-white/20 mx-auto mb-4" />
                        <p className="font-body text-2xl text-white/30 italic">
                          "Silence awaits your vision."
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                {/* The Controls */}
                <div className="space-y-12 flex flex-col justify-center">

                  {/* Upload */}
                  <div className="space-y-4">
                    <h3 className="text-2xl font-display text-gold-accent">1. The Source</h3>
                    <p className="font-body text-gray-400">Select the image you wish to transmute.</p>
                    <label className="block w-full cursor-pointer group">
                      <div className="w-full h-32 border border-white/10 bg-white/5 flex flex-col items-center justify-center transition-all duration-300 group-hover:bg-white/10 group-hover:border-gold-accent/50">
                        <input
                          type="file"
                          accept="image/*"
                          className="hidden"
                          onChange={handleImageUpload}
                        />
                        <Upload className="w-8 h-8 text-gold-accent mb-2 transition-transform group-hover:-translate-y-1" />
                        <span className="font-display text-sm text-gray-300 tracking-widest uppercase">
                          {uploadedImage ? "Change Image" : "Upload Image"}
                        </span>
                      </div>
                    </label>
                  </div>

                  {/* Settings */}
                  <div className="space-y-6">
                    <h3 className="text-2xl font-display text-gold-accent">2. The Complexity</h3>
                    <div className="flex flex-wrap gap-4">
                      {/* Preserving exactly the titles: Low, Medium, High */}
                      <QualityButton value="low" label="Low" />
                      <QualityButton value="medium" label="Medium" />
                      <QualityButton value="high" label="High" />
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="text-2xl font-display text-gold-accent">3. The Dialect</h3>
                    <div className="relative">
                      <select
                        value={generatorSettings.palette}
                        onChange={(e) =>
                          setGeneratorSettings((prev) => ({
                            ...prev,
                            palette: e.target.value.toLowerCase(),
                          }))
                        }
                        className="w-full appearance-none bg-black/50 border border-white/20 px-6 py-4 font-body text-xl text-white outline-none focus:border-gold-accent transition-colors cursor-pointer"
                      >
                        <option value="math">Mathematical Symbols</option>
                        <option value="ascii">Classical ASCII</option>
                        <option value="greek">Greek Alphabet</option>
                      </select>
                      <div className="absolute right-6 top-1/2 -translate-y-1/2 pointer-events-none text-gold-accent">
                        ▼
                      </div>
                    </div>
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
          className="pt-40 min-h-screen flex flex-col items-center text-center px-6"
        >
          <h2 className="text-5xl md:text-6xl font-display text-gold-accent mb-12">
            The Philosophy
          </h2>
          <div className="max-w-4xl space-y-8 font-body text-xl text-gray-300 leading-relaxed text-left md:text-center">
            <p>
              In a world of pixels, we search for meaning. <strong className="text-white">Symbol Art</strong> is not just a generator;
              it is an exploration of the underlying mathematical beauty that governs our reality.
            </p>
            <p>
              By converting raw imagery into fundamental symbols, we strip away the noise and reveal the
              structural elegance hidden within. It is a tribute to the language of the universe.
            </p>
          </div>
        </div>
      )}

      {/* FOOTER: 'Where it is made' functionality preservation */}
      <footer className="w-full py-16 border-t border-white/5 mt-20">
        <div className="max-w-7xl mx-auto px-6 flex flex-col items-center space-y-8">
          <div className="text-3xl font-display text-gold-accent">Symbol Art</div>
          <div className="font-body text-gray-500 italic">"Where Logic Meets Emotion"</div>
          <div className="flex gap-8">
            <a
              href="https://www.linkedin.com/in/rizulgarg2159"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-400 hover:text-gold-accent transition-colors"
            >
              <Linkedin className="w-6 h-6" />
            </a>
          </div>
          {/* Preserved attribution */}
          <p className="text-sm text-gray-600 font-display tracking-widest uppercase mt-8">
            Created by Rizul Garg
          </p>
        </div>
      </footer>
    </div>
  );

  return (
    <div className="bg-midnight text-white min-h-screen">
      {renderNav()}
      {renderSection()}
    </div>
  );
};

export default App;
