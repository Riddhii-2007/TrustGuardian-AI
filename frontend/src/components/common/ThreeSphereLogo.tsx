import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

// ===============================================
// TrustGuardian AI — WebGL Animated Shield Core Logo
// ===============================================

interface ThreeSphereLogoProps {
  className?: string;
}

export const ThreeSphereLogo: React.FC<ThreeSphereLogoProps> = ({ className = 'w-24 h-24' }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const container = containerRef.current;
    const width = container.clientWidth || 96;
    const height = container.clientHeight || 96;

    // 1. Scene Setup
    const scene = new THREE.Scene();

    // 2. Camera Setup (Orthographic or close Perspective to prevent cropping)
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.z = 4.2;

    // 3. Renderer Setup
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // 4. Central Core - Wireframe Icosahedron
    const coreGeometry = new THREE.IcosahedronGeometry(1.0, 2);
    const coreMaterial = new THREE.MeshPhongMaterial({
      color: 0x4F8CFF, // Trust Blue
      wireframe: true,
      transparent: true,
      opacity: 0.75,
      emissive: 0x4F8CFF,
      emissiveIntensity: 0.5,
    });
    const coreMesh = new THREE.Mesh(coreGeometry, coreMaterial);
    scene.add(coreMesh);

    // 5. Inner Glow Sphere
    const innerGeometry = new THREE.SphereGeometry(0.65, 32, 32);
    const innerMaterial = new THREE.MeshPhongMaterial({
      color: 0x8B5CF6, // AI Purple
      transparent: true,
      opacity: 0.35,
    });
    const innerSphereMesh = new THREE.Mesh(innerGeometry, innerMaterial);
    scene.add(innerSphereMesh);

    // 6. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0x4F8CFF, 2, 50);
    pointLight.position.set(5, 5, 5);
    scene.add(pointLight);

    const purpleLight = new THREE.PointLight(0x8B5CF6, 2, 50);
    purpleLight.position.set(-5, -5, 5);
    scene.add(purpleLight);

    // 7. Resize Handler
    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    // 8. Animation Loop
    let animationFrameId: number;
    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);

      // Rotate meshes
      coreMesh.rotation.y += 0.008;
      coreMesh.rotation.x += 0.003;
      innerSphereMesh.rotation.z += 0.012;

      // Pulse Core scale over time
      const pulse = 1.0 + Math.sin(Date.now() * 0.0035) * 0.06;
      coreMesh.scale.set(pulse, pulse, pulse);
      innerSphereMesh.scale.set(pulse, pulse, pulse);

      renderer.render(scene, camera);
    };
    animate();

    // 9. Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
      
      coreGeometry.dispose();
      coreMaterial.dispose();
      innerGeometry.dispose();
      innerMaterial.dispose();
      renderer.dispose();
      
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  return (
    <div className={`relative flex items-center justify-center ${className}`}>
      {/* 3D WebGL Canvas Container */}
      <div ref={containerRef} className="absolute inset-0 w-full h-full z-0 pointer-events-none" />

      {/* Futuristic Shield Overlay Graphic */}
      <div className="absolute inset-0 z-10 flex items-center justify-center pointer-events-none">
        <svg 
          className="w-11/12 h-11/12 text-cyan-400/80 drop-shadow-[0_0_15px_rgba(6,182,212,0.4)] animate-[pulse_3s_ease-in-out_infinite]"
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          strokeWidth="1.25"
        >
          {/* Shield Outline */}
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.57-.598-3.75h-.152c-3.196 0-6.1-1.249-8.25-3.286zm0 3.036v13.5" 
          />
        </svg>
      </div>

      {/* Futuristic concentric scanning HUD rings */}
      <div className="absolute inset-0 border border-dashed border-cyan-500/20 rounded-full animate-[spin_30s_linear_infinite]" />
      <div className="absolute inset-1.5 border border-dotted border-blue-500/10 rounded-full animate-[spin_15s_linear_infinite_reverse]" />
    </div>
  );
};
