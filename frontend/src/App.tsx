import { Navbar } from './components/Navbar';
import { Hero } from './components/Hero';
import { Capabilities } from './components/Capabilities';
import { Architecture } from './components/Architecture';
import { EvalHarness } from './components/EvalHarness';
import { Footer } from './components/Footer';
import { motion, useScroll, useTransform } from 'motion/react';
import Spline from '@splinetool/react-spline';

const SplineBackground = () => {
  const { scrollYProgress } = useScroll();
  // Zooms from 1.0 to 1.3 at halfway down the page, then back down to 1.0 at the bottom
  const scale = useTransform(scrollYProgress, [0, 0.5, 1], [1, 1.3, 1]);

  return (
    <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
      <motion.div 
        style={{ scale }} 
        className="w-full h-full pointer-events-auto"
      >
        <Spline scene="https://prod.spline.design/WQqN9roZiflMXT2R/scene.splinecode" />
      </motion.div>
    </div>
  );
};

export default function App() {
  return (
    <div className="min-h-screen bg-background text-ink font-sans flex flex-col relative">
      <SplineBackground />
      <Navbar />
      <main className="flex-1 mt-[80px] pointer-events-none">
        <Hero />
        <Capabilities />
        <Architecture />
        <EvalHarness />
      </main>
      <Footer />
    </div>
  );
}
