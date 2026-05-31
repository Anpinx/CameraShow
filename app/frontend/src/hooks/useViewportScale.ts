import { useEffect, useRef } from 'react';

/** 将 1920×1080 设计画布等比缩放至当前视口 */
export function useViewportScale() {
  const canvasRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const updateScale = () => {
      const scale = Math.min(window.innerWidth / 1920, window.innerHeight / 1080);
      canvas.style.transform = `scale(${scale})`;
    };

    updateScale();
    window.addEventListener('resize', updateScale);
    return () => window.removeEventListener('resize', updateScale);
  }, []);

  return canvasRef;
}
