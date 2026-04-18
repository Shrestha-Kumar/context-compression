import { Navbar } from '../components/landing/Navbar';
import { Hero } from '../components/landing/Hero';
import { Capabilities } from '../components/landing/Capabilities';
import { Architecture } from '../components/landing/Architecture';
import { EvalHarness } from '../components/landing/EvalHarness';
import { Footer } from '../components/landing/Footer';
import { motion, useScroll, useTransform } from 'motion/react';
import Spline from '@splinetool/react-spline';

const SplineBackground = () => {
  const { scrollYProgress } = useScroll();
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

export default function Landing() {
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
