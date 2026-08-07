import React, { useEffect, useRef } from 'react';

// ==========================================
// TrustGuardian AI — Premium Glowing Custom Cursor
// Smooth easing, hover magnetism, and click ripples
// ==========================================

export const CustomCursor: React.FC = () => {
  const cursorDotRef = useRef<HTMLDivElement | null>(null);
  const cursorRingRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const dot = cursorDotRef.current;
    const ring = cursorRingRef.current;
    if (!dot || !ring) return;

    let mouseX = -100;
    let mouseY = -100;
    let ringX = -100;
    let ringY = -100;
    let isHovered = false;

    const onMouseMove = (e: MouseEvent) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
    };

    const onMouseDown = () => {
      if (ring) ring.style.transform = 'translate(-50%, -50%) scale(0.75)';
    };

    const onMouseUp = () => {
      if (ring) ring.style.transform = `translate(-50%, -50%) ${isHovered ? 'scale(1.4)' : 'scale(1)'}`;
    };

    // Click expanding ripple
    const createRipple = () => {
      const ripple = document.createElement('div');
      ripple.className = 'fixed rounded-full pointer-events-none -translate-x-1/2 -translate-y-1/2 bg-cyan-400/20 border border-cyan-400/40 z-[99999]';
      ripple.style.left = `${mouseX}px`;
      ripple.style.top = `${mouseY}px`;
      ripple.style.width = '0px';
      ripple.style.height = '0px';
      ripple.style.transition = 'width 0.45s cubic-bezier(0.1, 0.8, 0.3, 1), height 0.45s cubic-bezier(0.1, 0.8, 0.3, 1), opacity 0.45s ease-out';
      document.body.appendChild(ripple);

      // Force style recalculation
      requestAnimationFrame(() => {
        ripple.style.width = '80px';
        ripple.style.height = '80px';
        ripple.style.opacity = '0';
      });

      setTimeout(() => {
        ripple.remove();
      }, 500);
    };

    const onClick = () => {
      createRipple();
    };

    // Intercept hover elements
    const addHoverListeners = () => {
      const targets = document.querySelectorAll(
        'button, a, input, select, textarea, [role="button"], .clickable, .glass-card, .nav-item-glow'
      );

      const handleEnter = () => {
        isHovered = true;
        if (ring) {
          ring.style.width = '52px';
          ring.style.height = '52px';
          ring.style.borderColor = 'rgba(6, 182, 212, 0.85)';
          ring.style.backgroundColor = 'rgba(6, 182, 212, 0.06)';
          ring.style.transform = 'translate(-50%, -50%) scale(1.4)';
        }
        if (dot) {
          dot.style.transform = 'translate(-50%, -50%) scale(1.5)';
          dot.style.backgroundColor = '#22d3ee';
        }
      };

      const handleLeave = () => {
        isHovered = false;
        if (ring) {
          ring.style.width = '32px';
          ring.style.height = '32px';
          ring.style.borderColor = 'rgba(6, 182, 212, 0.4)';
          ring.style.backgroundColor = 'transparent';
          ring.style.transform = 'translate(-50%, -50%) scale(1)';
        }
        if (dot) {
          dot.style.transform = 'translate(-50%, -50%) scale(1)';
          dot.style.backgroundColor = '#06b6d4';
        }
      };

      targets.forEach((t) => {
        t.addEventListener('mouseenter', handleEnter);
        t.addEventListener('mouseleave', handleLeave);
      });

      return () => {
        targets.forEach((t) => {
          t.removeEventListener('mouseenter', handleEnter);
          t.removeEventListener('mouseleave', handleLeave);
        });
      };
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mouseup', onMouseUp);
    window.addEventListener('click', onClick);

    let removeListeners = addHoverListeners();

    // Poll periodically to attach to dynamic React DOM nodes
    const intervalId = setInterval(() => {
      removeListeners();
      removeListeners = addHoverListeners();
    }, 1000);

    let frameId: number;
    const loop = () => {
      // Easing calculation for ring lag
      const ease = 0.16;
      ringX += (mouseX - ringX) * ease;
      ringY += (mouseY - ringY) * ease;

      if (dot) {
        dot.style.transform = `translate3d(${mouseX}px, ${mouseY}px, 0)`;
      }
      if (ring) {
        ring.style.transform = `translate3d(${ringX}px, ${ringY}px, 0)`;
      }

      frameId = requestAnimationFrame(loop);
    };

    loop();

    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mouseup', onMouseUp);
      window.removeEventListener('click', onClick);
      clearInterval(intervalId);
      removeListeners();
      cancelAnimationFrame(frameId);
    };
  }, []);

  return (
    <>
      <style>{`
        @media (pointer: fine) {
          body, button, a, input, select, textarea, [role="button"], .clickable {
            cursor: none !important;
          }
        }
      `}</style>

      {/* Glowing cursor center pointer */}
      <div
        ref={cursorDotRef}
        className="fixed top-0 left-0 w-2.5 h-2.5 bg-cyan-500 rounded-full pointer-events-none z-[99999] hidden lg:block -translate-x-1/2 -translate-y-1/2"
        style={{
          boxShadow: '0 0 10px #06b6d4, 0 0 20px #0891b2',
          willChange: 'transform',
        }}
      />

      {/* Floating outer lagging circle */}
      <div
        ref={cursorRingRef}
        className="fixed top-0 left-0 w-8 h-8 border border-cyan-500/40 rounded-full pointer-events-none z-[99998] hidden lg:block -translate-x-1/2 -translate-y-1/2 transition-all duration-300 ease-out"
        style={{
          willChange: 'transform',
        }}
      />
    </>
  );
};
