import { motion, AnimatePresence } from 'motion/react';
import Spline from '@splinetool/react-spline';
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../store/appStore';

export function TransitionOverlay() {
  const { isTransitioning, targetRoute, endTransition } = useAppStore();
  const navigate = useNavigate();

  useEffect(() => {
    if (isTransitioning && targetRoute) {
      // Stage 3 -> Stage 4: After Spline drops in and waits, push the route.
      const routeTimer = setTimeout(() => {
        navigate(targetRoute);
      }, 2500); // Route visually changes underneath exactly at 2.5s.

      // Release overlay.
      const finishTimer = setTimeout(() => {
        endTransition();
      }, 4000); // 4 seconds total transition lock.

      return () => {
        clearTimeout(routeTimer);
        clearTimeout(finishTimer);
      };
    }
  }, [isTransitioning, targetRoute, navigate, endTransition]);

  return (
    <AnimatePresence>
      {isTransitioning && (
        <motion.div
          className="fixed inset-0 z-[100] pointer-events-auto flex items-center justify-center bg-black"
          initial={{ clipPath: "circle(0% at center)" }}
          animate={{ clipPath: "circle(150% at center)" }}
          exit={{ opacity: 0, transition: { duration: 0.5 } }}
          transition={{ duration: 0.8, ease: "easeInOut" }}
        >
          {/* Transition Spline - fully interactive and centered */}
          <motion.div
            className="w-full h-full flex items-center justify-center pointer-events-auto cursor-default"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 1.1, opacity: 0 }}
            transition={{ duration: 0.6 }}
          >
            <Spline scene="https://prod.spline.design/3PFOEhXBsBl8HlYU/scene.splinecode" />
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
