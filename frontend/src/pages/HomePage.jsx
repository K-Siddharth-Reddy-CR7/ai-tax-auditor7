import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import * as THREE from 'three';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { ScrollToPlugin } from 'gsap/ScrollToPlugin';
import {
  ShieldCheck, Globe, FileText, Layers, Zap,
  ChevronDown, ArrowRight, Scale, BookOpen, Search,
  BarChart2, Lock, TrendingUp
} from 'lucide-react';

gsap.registerPlugin(ScrollTrigger, ScrollToPlugin);

// ====================== 3D HERO SCENE ======================
function HeroThreeScene({ theme }) {
  const mountRef = useRef(null);
  const sceneRef = useRef(null);

  useEffect(() => {
    const el = mountRef.current;
    if (!el) return;
    const W = el.clientWidth || window.innerWidth;
    const H = el.clientHeight || window.innerHeight;

    // Scene
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, W / H, 1, 2000);
    camera.position.set(0, 0, 340);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(W, H);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);
    el.innerHTML = '';
    el.appendChild(renderer.domElement);

    // Ambient + directional lights
    scene.add(new THREE.AmbientLight(0xffffff, 0.7));
    const dir = new THREE.DirectionalLight(0x4488ff, 2.0);
    dir.position.set(120, 100, 180);
    scene.add(dir);
    const dir2 = new THREE.DirectionalLight(0x22ccaa, 1.0);
    dir2.position.set(-160, -80, -100);
    scene.add(dir2);

    // === CENTRAL GLOBE ===
    const globeGroup = new THREE.Group();
    scene.add(globeGroup);

    // Land masses drawn as canvas texture
    const canvas = document.createElement('canvas');
    canvas.width = 1024;
    canvas.height = 512;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#0a0d14';
    ctx.fillRect(0, 0, 1024, 512);

    // Draw continents (simplified polygons)
    ctx.fillStyle = '#1a2540';
    const regions = [
      // North America
      [[170, 80], [260, 90], [270, 160], [210, 200], [185, 180], [165, 130]],
      // South America
      [[210, 225], [270, 220], [275, 360], [230, 380], [200, 350], [195, 280]],
      // Europe
      [[440, 80], [520, 70], [530, 140], [490, 150], [450, 130]],
      // Africa
      [[440, 160], [530, 155], [550, 310], [500, 350], [440, 330], [420, 240]],
      // Asia
      [[530, 60], [760, 55], [800, 140], [750, 200], [680, 230], [570, 210], [530, 160]],
      // Australia
      [[720, 295], [810, 285], [820, 350], [760, 370], [710, 350]],
      // Greenland
      [[255, 40], [310, 30], [315, 80], [260, 85]],
    ];
    regions.forEach(pts => {
      ctx.beginPath();
      ctx.moveTo(pts[0][0] * 2, pts[0][1] * 2);
      pts.slice(1).forEach(p => ctx.lineTo(p[0] * 2, p[1] * 2));
      ctx.closePath();
      ctx.fill();
    });

    // Grid lines
    ctx.strokeStyle = 'rgba(59,130,246,0.12)';
    ctx.lineWidth = 1;
    for (let i = 0; i < 12; i++) {
      ctx.beginPath();
      ctx.moveTo((i / 12) * 1024, 0);
      ctx.lineTo((i / 12) * 1024, 512);
      ctx.stroke();
    }
    for (let i = 0; i < 6; i++) {
      ctx.beginPath();
      ctx.moveTo(0, (i / 6) * 512);
      ctx.lineTo(1024, (i / 6) * 512);
      ctx.stroke();
    }

    const globeTexture = new THREE.CanvasTexture(canvas);
    const globeGeo = new THREE.SphereGeometry(80, 64, 64);
    const globeMat = new THREE.MeshStandardMaterial({
      map: globeTexture,
      roughness: 0.55,
      metalness: 0.15
    });
    const globe = new THREE.Mesh(globeGeo, globeMat);
    globeGroup.add(globe);

    // Atmosphere glow
    const atmosGeo = new THREE.SphereGeometry(82.5, 48, 48);
    const atmosMat = new THREE.MeshBasicMaterial({
      color: 0x1a4cff,
      transparent: true,
      opacity: 0.08,
      side: THREE.BackSide
    });
    globeGroup.add(new THREE.Mesh(atmosGeo, atmosMat));

    // === ORBITING DOCUMENT / POLICY CARDS (3D) ===
    const orbitGroup = new THREE.Group();
    scene.add(orbitGroup);

    const ORBIT_ITEMS = [
      { label: 'Import Duty\n8.5%', color: 0xf59e0b, orbit: 130, speed: 0.008 },
      { label: 'VAT 18%', color: 0x3b82f6, orbit: 160, speed: -0.006 },
      { label: 'Trade Policy\nAct §12', color: 0x10b981, orbit: 140, speed: 0.011 },
      { label: 'HS Code\n8471.30', color: 0xa855f7, orbit: 125, speed: -0.009 },
      { label: 'Customs\nClearance', color: 0xf43f5e, orbit: 155, speed: 0.007 },
      { label: 'Compliance\nAudit OK', color: 0x06b6d4, orbit: 145, speed: -0.013 },
    ];

    const orbitMeshes = ORBIT_ITEMS.map((item, i) => {
      const cardGeo = new THREE.BoxGeometry(28, 16, 2);
      const cardMat = new THREE.MeshStandardMaterial({
        color: 0x0d1424,
        roughness: 0.2,
        metalness: 0.8,
        transparent: true,
        opacity: 0.92
      });
      const card = new THREE.Mesh(cardGeo, cardMat);

      // Wireframe accent
      const wgeo = new THREE.BoxGeometry(28.5, 16.5, 2.5);
      const wmat = new THREE.MeshBasicMaterial({ color: item.color, wireframe: true, transparent: true, opacity: 0.6 });
      const wire = new THREE.Mesh(wgeo, wmat);
      card.add(wire);

      // Position in orbit
      const angle = (i / ORBIT_ITEMS.length) * Math.PI * 2;
      const tiltAngle = ((i % 3) - 1) * 0.3;
      card.position.set(
        Math.cos(angle) * item.orbit,
        Math.sin(tiltAngle) * 40 + (i % 2 === 0 ? 20 : -20),
        Math.sin(angle) * item.orbit
      );
      card.userData = { baseAngle: angle, orbit: item.orbit, speed: item.speed, color: item.color, tiltAngle };
      orbitGroup.add(card);
      return card;
    });

    // === TRADE ROUTE ARCS (curved lines) ===
    const arcGroup = new THREE.Group();
    scene.add(arcGroup);

    const ROUTES = [
      { from: [37, -95], to: [20, 79] },
      { from: [51, 10], to: [35, 135] },
      { from: [1, 103], to: [56, -106] },
      { from: [-25, 133], to: [55, 37] },
      { from: [23, 53], to: [46, 2] },
    ];

    function latLng(lat, lng, r) {
      const phi = (90 - lat) * (Math.PI / 180);
      const theta = (lng + 180) * (Math.PI / 180);
      return new THREE.Vector3(
        -(r * Math.sin(phi) * Math.cos(theta)),
        r * Math.cos(phi),
        r * Math.sin(phi) * Math.sin(theta)
      );
    }

    const arcPulses = [];

    ROUTES.forEach(({ from, to }, idx) => {
      const p0 = latLng(from[0], from[1], 80);
      const p1 = latLng(to[0], to[1], 80);
      const mid = p0.clone().add(p1).multiplyScalar(0.5);
      const dist = p0.distanceTo(p1);
      mid.normalize().multiplyScalar(80 + dist * 0.32);

      const curve = new THREE.QuadraticBezierCurve3(p0, mid, p1);
      const points = curve.getPoints(60);
      const geo = new THREE.BufferGeometry().setFromPoints(points);
      const mat = new THREE.LineBasicMaterial({
        color: [0x3b82f6, 0x10b981, 0xf59e0b, 0xa855f7, 0x06b6d4][idx % 5],
        transparent: true,
        opacity: 0.5
      });
      arcGroup.add(new THREE.Line(geo, mat));

      // Pulse dot
      const pGeo = new THREE.SphereGeometry(1.2, 8, 8);
      const pMat = new THREE.MeshBasicMaterial({ color: [0x3b82f6, 0x10b981, 0xf59e0b, 0xa855f7, 0x06b6d4][idx % 5] });
      const pulse = new THREE.Mesh(pGeo, pMat);
      arcGroup.add(pulse);
      arcPulses.push({ mesh: pulse, curve, progress: idx * 0.18 });
    });

    // === FLOATING PARTICLES (stars / data nodes) ===
    const particleCount = 200;
    const pPositions = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount; i++) {
      const r = 160 + Math.random() * 180;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      pPositions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      pPositions[i * 3 + 1] = r * Math.cos(phi);
      pPositions[i * 3 + 2] = r * Math.sin(phi) * Math.sin(theta);
    }
    const pGeo = new THREE.BufferGeometry();
    pGeo.setAttribute('position', new THREE.BufferAttribute(pPositions, 3));
    const pMat = new THREE.PointsMaterial({ color: 0x3b82f6, size: 1.2, transparent: true, opacity: 0.5 });
    const particles = new THREE.Points(pGeo, pMat);
    scene.add(particles);

    sceneRef.current = { scene, camera, renderer, globeGroup, orbitGroup, arcGroup, arcPulses, orbitMeshes };

    // === ANIMATION LOOP ===
    let t = 0;
    let animId;
    const animate = () => {
      t += 0.01;
      animId = requestAnimationFrame(animate);

      // Globe slow rotation
      globeGroup.rotation.y += 0.0022;
      arcGroup.rotation.y = globeGroup.rotation.y;

      // Orbit cards revolve
      orbitMeshes.forEach((card, i) => {
        const { baseAngle, orbit, speed, tiltAngle } = card.userData;
        const a = baseAngle + t * speed * 100 * 0.01;
        card.position.x = Math.cos(a) * orbit;
        card.position.z = Math.sin(a) * orbit;
        card.lookAt(0, 0, 0);
        // Subtle float
        card.position.y = Math.sin(tiltAngle + t * 0.4 + i) * 30 + (i % 2 === 0 ? 15 : -15);
      });

      // Arc pulses
      arcPulses.forEach(p => {
        p.progress = (p.progress + 0.006) % 1;
        const pt = p.curve.getPoint(p.progress);
        p.mesh.position.copy(pt);
      });

      // Particles slow spin
      particles.rotation.y += 0.0006;

      renderer.render(scene, camera);
    };
    animate();

    // GSAP camera entrance zoom
    gsap.from(camera.position, { z: 550, duration: 2.2, ease: 'power3.out' });
    gsap.from(globeGroup.rotation, { y: -Math.PI * 0.5, duration: 2.2, ease: 'power3.out' });

    // Resize
    const ro = new ResizeObserver(() => {
      const nw = el.clientWidth;
      const nh = el.clientHeight;
      camera.aspect = nw / nh;
      camera.updateProjectionMatrix();
      renderer.setSize(nw, nh);
    });
    ro.observe(el);

    // Mouse parallax
    const handleMove = (e) => {
      const mx = (e.clientX / window.innerWidth - 0.5) * 0.25;
      const my = (e.clientY / window.innerHeight - 0.5) * 0.15;
      gsap.to(globeGroup.rotation, { x: -my, duration: 1.2, ease: 'power1.out', overwrite: true });
    };
    window.addEventListener('mousemove', handleMove);

    return () => {
      cancelAnimationFrame(animId);
      ro.disconnect();
      window.removeEventListener('mousemove', handleMove);
      renderer.dispose();
    };
  }, []);

  return <div ref={mountRef} style={{ width: '100%', height: '100%' }} />;
}

// ====================== FEATURE 3D ICON ======================
function PolicyIcon3D({ color, size = 80 }) {
  const mountRef = useRef(null);

  useEffect(() => {
    const el = mountRef.current;
    if (!el) return;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, 1, 1, 200);
    camera.position.z = 40;
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(size, size);
    renderer.setClearColor(0, 0);
    el.appendChild(renderer.domElement);

    scene.add(new THREE.AmbientLight(0xffffff, 0.8));
    const dl = new THREE.DirectionalLight(color, 2.5);
    dl.position.set(10, 10, 10);
    scene.add(dl);

    // Main shape (document / shield hybrid)
    const boxGeo = new THREE.BoxGeometry(12, 16, 2.5);
    const boxMat = new THREE.MeshStandardMaterial({
      color: 0x0d1424,
      roughness: 0.2,
      metalness: 0.9
    });
    const box = new THREE.Mesh(boxGeo, boxMat);
    scene.add(box);

    // Wireframe
    const wgeo = new THREE.BoxGeometry(12.4, 16.4, 2.9);
    const wmat = new THREE.MeshBasicMaterial({ color, wireframe: true, transparent: true, opacity: 0.7 });
    scene.add(new THREE.Mesh(wgeo, wmat));

    // Glow sphere
    const sg = new THREE.SphereGeometry(4, 16, 16);
    const sm = new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 0.5, transparent: true, opacity: 0.3 });
    const sp = new THREE.Mesh(sg, sm);
    sp.position.set(0, -8, 0);
    scene.add(sp);

    let animId;
    let t = 0;
    const animate = () => {
      t += 0.018;
      box.rotation.y = Math.sin(t) * 0.4;
      box.rotation.x = Math.cos(t * 0.7) * 0.15;
      renderer.render(scene, camera);
      animId = requestAnimationFrame(animate);
    };
    animate();

    return () => {
      cancelAnimationFrame(animId);
      renderer.dispose();
    };
  }, [color, size]);

  return <div ref={mountRef} style={{ width: size, height: size }} />;
}

// ====================== STATS COUNTER ======================
function CountUp({ to, suffix = '', duration = 2 }) {
  const ref = useRef(null);
  useEffect(() => {
    const obj = { val: 0 };
    const trigger = ScrollTrigger.create({
      trigger: ref.current,
      start: 'top 85%',
      once: true,
      onEnter: () => {
        gsap.to(obj, {
          val: to,
          duration,
          ease: 'power2.out',
          onUpdate: () => {
            if (ref.current) ref.current.textContent = Math.round(obj.val).toLocaleString() + suffix;
          }
        });
      }
    });
    return () => trigger.kill();
  }, [to, suffix, duration]);
  return <span ref={ref}>0{suffix}</span>;
}

// ====================== HOME PAGE ======================
export default function HomePage() {
  const navigate = useNavigate();
  const heroRef = useRef(null);
  const heroTextRef = useRef(null);
  const ctaBtnRef = useRef(null);
  const featuresRef = useRef(null);
  const statsRef = useRef(null);
  const agentsRef = useRef(null);
  const ctaRef = useRef(null);
  const navRef = useRef(null);
  const [theme, setTheme] = useState('dark');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  useEffect(() => {
    // Nav entrance
    gsap.fromTo(navRef.current,
      { y: -40, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.7, ease: 'power3.out' }
    );

    // Hero text stagger entrance
    const heroEls = heroTextRef.current?.querySelectorAll('.hp-anim');
    if (heroEls) {
      gsap.fromTo(heroEls,
        { y: 40, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.8, stagger: 0.12, ease: 'power3.out', delay: 0.3 }
      );
    }

    // CTA hover effect
    const btn = ctaBtnRef.current;
    if (btn) {
      btn.addEventListener('mouseenter', () => gsap.to(btn, { scale: 1.04, duration: 0.2 }));
      btn.addEventListener('mouseleave', () => gsap.to(btn, { scale: 1, duration: 0.2 }));
    }

    // Feature cards scroll reveal
    const featureCards = featuresRef.current?.querySelectorAll('.hp-feature-card');
    if (featureCards) {
      gsap.fromTo(featureCards,
        { y: 60, opacity: 0 },
        {
          y: 0, opacity: 1, duration: 0.7, stagger: 0.12,
          ease: 'power3.out',
          scrollTrigger: { trigger: featuresRef.current, start: 'top 75%', once: true }
        }
      );
    }

    // Stats reveal
    if (statsRef.current) {
      gsap.fromTo(statsRef.current,
        { opacity: 0, y: 30 },
        { opacity: 1, y: 0, duration: 0.8, ease: 'power3.out',
          scrollTrigger: { trigger: statsRef.current, start: 'top 80%', once: true } }
      );
    }

    // Agent steps cascade
    const agentSteps = agentsRef.current?.querySelectorAll('.hp-agent-step');
    if (agentSteps) {
      gsap.fromTo(agentSteps,
        { x: -50, opacity: 0 },
        {
          x: 0, opacity: 1, duration: 0.6, stagger: 0.1,
          ease: 'power2.out',
          scrollTrigger: { trigger: agentsRef.current, start: 'top 70%', once: true }
        }
      );
    }

    // CTA section reveal
    if (ctaRef.current) {
      gsap.fromTo(ctaRef.current,
        { opacity: 0, scale: 0.96 },
        { opacity: 1, scale: 1, duration: 0.8, ease: 'power3.out',
          scrollTrigger: { trigger: ctaRef.current, start: 'top 80%', once: true } }
      );
    }

    // Nav background on scroll
    ScrollTrigger.create({
      start: 'top -60',
      onUpdate: (self) => {
        if (navRef.current) {
          navRef.current.style.background = self.progress > 0
            ? 'rgba(12,13,18,0.97)'
            : 'transparent';
          navRef.current.style.backdropFilter = self.progress > 0 ? 'blur(16px)' : 'none';
          navRef.current.style.borderBottom = self.progress > 0 ? '1px solid rgba(35,41,56,0.8)' : '1px solid transparent';
        }
      }
    });

    return () => {
      ScrollTrigger.getAll().forEach(t => t.kill());
    };
  }, []);

  const scrollToSection = (id) => {
    gsap.to(window, { scrollTo: `#${id}`, duration: 0.9, ease: 'power3.inOut' });
  };

  const FEATURES = [
    {
      icon: <Globe size={24} style={{ color: '#3b82f6' }} />,
      color: 0x3b82f6,
      title: 'Geographical Trade Intelligence',
      desc: 'Interactive 3D world map with real-time trade route visualization across 40+ customs jurisdictions. Identify corridors, tariff rates, and VAT schedules at a glance.'
    },
    {
      icon: <Scale size={24} style={{ color: '#10b981' }} />,
      color: 0x10b981,
      title: 'Precise Customs Valuation',
      desc: 'Statutory assessable value calculation per WTO customs valuation rules — CIF basis, import duty rates, GST/VAT stacking, with full breakdown to per-unit cost.'
    },
    {
      icon: <BookOpen size={24} style={{ color: '#f59e0b' }} />,
      color: 0xf59e0b,
      title: 'RAG Policy Compliance Engine',
      desc: 'TF-IDF dense vector retrieval over 240+ active trade compliance policies. Flags BIS, CE, FDA permits and bilateral FTA exemptions automatically.'
    },
    {
      icon: <Search size={24} style={{ color: '#a855f7' }} />,
      color: 0xa855f7,
      title: 'HS-6 Product Classification',
      desc: 'Fuzzy-match commercial product descriptions against 1,200+ HS-6 classified commodities using the global harmonized tariff schedule catalog.'
    },
    {
      icon: <Layers size={24} style={{ color: '#f43f5e' }} />,
      color: 0xf43f5e,
      title: 'Batch Audit (400 Transactions)',
      desc: 'Bulk-process entire manifests of 400 trade transactions simultaneously. Export compliance certificates per shipment or aggregate analytics.'
    },
    {
      icon: <Lock size={24} style={{ color: '#06b6d4' }} />,
      color: 0x06b6d4,
      title: 'Cryptographic Audit ID',
      desc: 'Every audit result is stamped with a cryptographic SHA-based audit identifier ensuring full provenance traceability for regulatory submission.'
    }
  ];

  const AGENTS = [
    { num: '01', name: 'Input Agent', tag: 'Sanitization & Validation', color: '#60a5fa', desc: 'Normalizes product specifications, quantities, declared unit values, and CIF shipping freight terms into a clean structured payload.' },
    { num: '02', name: 'Product Agent', tag: 'HS-6 Classification', color: '#38bdf8', desc: 'Fuzzy-matches commercial descriptions against 1,200 catalog commodities using token overlap and Levenshtein distance to assign HS Code.' },
    { num: '03', name: 'RAG Policy Agent', tag: 'Vector Regulatory Search', color: '#f59e0b', desc: 'Executes dense TF-IDF cosine similarity retrieval over 240 compliance rules, surfacing the most relevant policy clause for the shipment.' },
    { num: '04', name: 'Tax Agent', tag: 'Tariff Schedule Match', color: '#a855f7', desc: 'Looks up statutory import duty percentage, national GST/VAT rate, and local currency from the jurisdictional customs tariff schedule database.' },
    { num: '05', name: 'Calculation Agent', tag: 'Customs Valuation Engine', color: '#10b981', desc: 'Computes assessable customs value (CIF), exact duty amount, taxable base, statutory VAT, and total landed cost with per-unit breakdowns.' },
    { num: '06', name: 'Report Agent', tag: 'Provenance & Verdict', color: '#34d399', desc: 'Compiles full audit provenance trace, assigns cryptographic audit ID, timestamps the transaction, and outputs the final compliance verdict.' },
  ];

  return (
    <div className="hp-container" style={{ background: '#0c0d12', minHeight: '100vh', color: '#f3f4f6', overflowX: 'hidden' }}>
      {/* ===== NAVIGATION ===== */}
      <nav ref={navRef} style={{
        position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 48px', height: 68,
        transition: 'background 0.3s ease, backdrop-filter 0.3s ease, border-bottom 0.3s ease',
        borderBottom: '1px solid transparent'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 34, height: 34, borderRadius: 8,
            background: 'rgba(59,130,246,0.15)', border: '1px solid rgba(59,130,246,0.4)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#60a5fa'
          }}>
            <ShieldCheck size={18} />
          </div>
          <span style={{ fontWeight: 700, fontSize: 15, letterSpacing: '-0.01em' }}>LEXITAX AUDIT</span>
          <span style={{
            fontSize: 10, fontWeight: 600, padding: '2px 7px', borderRadius: 4,
            background: 'rgba(59,130,246,0.12)', border: '1px solid rgba(59,130,246,0.3)',
            color: '#60a5fa', textTransform: 'uppercase', letterSpacing: '0.05em'
          }}>Multi-Agent RAG</span>
        </div>

        <div style={{ display: 'flex', gap: 32, alignItems: 'center' }}>
          {['features', 'pipeline', 'stats'].map(id => (
            <button key={id} onClick={() => scrollToSection(id)} style={{
              background: 'none', border: 'none', color: '#9ca3af', fontSize: 13, fontWeight: 500,
              cursor: 'pointer', textTransform: 'capitalize', transition: 'color 0.15s ease'
            }}
              onMouseEnter={e => e.target.style.color = '#f3f4f6'}
              onMouseLeave={e => e.target.style.color = '#9ca3af'}
            >
              {id === 'pipeline' ? 'How it Works' : id.charAt(0).toUpperCase() + id.slice(1)}
            </button>
          ))}
          <button
            onClick={() => navigate('/audit')}
            style={{
              padding: '8px 20px', borderRadius: 7, fontSize: 13, fontWeight: 600,
              background: '#f3f4f6', color: '#0c0d12', border: 'none', cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: 6, transition: 'opacity 0.2s'
            }}
            onMouseEnter={e => e.currentTarget.style.opacity = '0.85'}
            onMouseLeave={e => e.currentTarget.style.opacity = '1'}
          >
            Open Audit Platform <ArrowRight size={13} />
          </button>
        </div>
      </nav>

      {/* ===== HERO SECTION ===== */}
      <section ref={heroRef} style={{ position: 'relative', height: '100vh', display: 'flex', alignItems: 'center' }}>
        {/* Three.js Background */}
        <div style={{ position: 'absolute', inset: 0, zIndex: 0 }}>
          <HeroThreeScene />
        </div>

        {/* Gradient overlay */}
        <div style={{
          position: 'absolute', inset: 0, zIndex: 1,
          background: 'radial-gradient(ellipse 70% 70% at 50% 50%, transparent 20%, rgba(12,13,18,0.65) 100%)'
        }} />

        {/* Hero Text */}
        <div ref={heroTextRef} style={{
          position: 'relative', zIndex: 2, maxWidth: 720,
          margin: '0 auto', padding: '0 24px', textAlign: 'center'
        }}>
          <div className="hp-anim" style={{
            display: 'inline-flex', alignItems: 'center', gap: 8,
            padding: '5px 14px', borderRadius: 20,
            background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.3)',
            color: '#60a5fa', fontSize: 12, fontWeight: 600,
            letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 24
          }}>
            <Zap size={11} fill="#60a5fa" /> AI-Powered Cross-Border Trade Compliance
          </div>

          <h1 className="hp-anim" style={{
            fontSize: 'clamp(38px, 6vw, 72px)', fontWeight: 700,
            letterSpacing: '-0.04em', lineHeight: 1.05, marginBottom: 24,
            color: '#f3f4f6'
          }}>
            Autonomous Tax &{' '}
            <span style={{
              background: 'linear-gradient(135deg, #3b82f6 0%, #06b6d4 50%, #10b981 100%)',
              WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent'
            }}>Trade Audit</span>
            <br />Intelligence
          </h1>

          <p className="hp-anim" style={{
            fontSize: 18, color: '#9ca3af', lineHeight: 1.7, marginBottom: 40,
            maxWidth: 560, margin: '0 auto 40px'
          }}>
            6-agent AI pipeline auditing cross-border shipments across 40 jurisdictions,
            240 compliance policies and 1,200 HS-classified commodities — in milliseconds.
          </p>

          <div className="hp-anim" style={{ display: 'flex', gap: 14, justifyContent: 'center', flexWrap: 'wrap' }}>
            <button
              ref={ctaBtnRef}
              onClick={() => navigate('/audit')}
              style={{
                padding: '14px 32px', borderRadius: 8, fontSize: 15, fontWeight: 700,
                background: '#f3f4f6', color: '#0c0d12', border: 'none', cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: 8,
                boxShadow: '0 0 40px rgba(59,130,246,0.2)'
              }}
            >
              Launch Audit Platform <ArrowRight size={16} />
            </button>
            <button
              onClick={() => scrollToSection('features')}
              style={{
                padding: '14px 28px', borderRadius: 8, fontSize: 14, fontWeight: 600,
                background: 'rgba(255,255,255,0.06)', color: '#e2e8f0',
                border: '1px solid rgba(255,255,255,0.12)', cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: 6, backdropFilter: 'blur(8px)',
                transition: 'background 0.2s'
              }}
              onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.1)'}
              onMouseLeave={e => e.currentTarget.style.background = 'rgba(255,255,255,0.06)'}
            >
              Explore Features
            </button>
          </div>
        </div>

        {/* Scroll indicator */}
        <div style={{
          position: 'absolute', bottom: 36, left: '50%', transform: 'translateX(-50%)',
          zIndex: 2, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8,
          color: '#64748b', fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase'
        }}>
          <span>Scroll to explore</span>
          <ChevronDown size={16} style={{ animation: 'bounce 1.6s infinite' }} />
        </div>
      </section>

      {/* ===== STATS SECTION ===== */}
      <section id="stats" ref={statsRef} style={{
        padding: '80px 48px',
        background: 'linear-gradient(180deg, rgba(12,13,18,1) 0%, rgba(18,21,29,1) 100%)',
        borderTop: '1px solid rgba(35,41,56,0.6)',
        borderBottom: '1px solid rgba(35,41,56,0.6)'
      }}>
        <div style={{
          maxWidth: 1100, margin: '0 auto',
          display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 32
        }}>
          {[
            { val: 1200, suffix: '+', label: 'HS-6 Classified Products', icon: <FileText size={18} style={{ color: '#3b82f6' }} /> },
            { val: 40, suffix: '', label: 'Customs Jurisdictions', icon: <Globe size={18} style={{ color: '#10b981' }} /> },
            { val: 240, suffix: '', label: 'Active Trade Policies', icon: <BookOpen size={18} style={{ color: '#f59e0b' }} /> },
            { val: 400, suffix: '', label: 'Batch Transactions Supported', icon: <BarChart2 size={18} style={{ color: '#a855f7' }} /> },
            { val: 6, suffix: '', label: 'Autonomous AI Agents', icon: <Zap size={18} style={{ color: '#06b6d4' }} /> },
          ].map((s, i) => (
            <div key={i} style={{ textAlign: 'center' }}>
              <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 12 }}>{s.icon}</div>
              <div style={{ fontSize: 'clamp(28px, 4vw, 48px)', fontWeight: 700, letterSpacing: '-0.03em', fontFamily: 'JetBrains Mono, monospace' }}>
                <CountUp to={s.val} suffix={s.suffix} />
              </div>
              <div style={{ fontSize: 13, color: '#64748b', marginTop: 6, fontWeight: 500 }}>{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ===== FEATURES SECTION ===== */}
      <section id="features" ref={featuresRef} style={{ padding: '100px 48px', maxWidth: 1200, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: 64 }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            padding: '4px 12px', borderRadius: 20, marginBottom: 20,
            background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.2)',
            color: '#60a5fa', fontSize: 11, fontWeight: 600, letterSpacing: '0.07em', textTransform: 'uppercase'
          }}>
            Core Capabilities
          </div>
          <h2 style={{ fontSize: 'clamp(28px, 4vw, 48px)', fontWeight: 700, letterSpacing: '-0.03em', marginBottom: 16 }}>
            Everything you need for<br />cross-border compliance
          </h2>
          <p style={{ fontSize: 16, color: '#9ca3af', maxWidth: 540, margin: '0 auto' }}>
            From HS classification to landed cost — a complete automated audit pipeline powered by specialized AI agents.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: 24 }}>
          {FEATURES.map((f, i) => (
            <div key={i} className="hp-feature-card" style={{
              padding: 28, borderRadius: 12,
              background: 'rgba(24,28,39,0.7)',
              border: '1px solid rgba(35,41,56,0.9)',
              backdropFilter: 'blur(8px)',
              cursor: 'default',
              transition: 'border-color 0.25s ease, transform 0.25s ease, box-shadow 0.25s ease'
            }}
              onMouseEnter={e => {
                e.currentTarget.style.borderColor = `rgba(${f.color === 0x3b82f6 ? '59,130,246' : f.color === 0x10b981 ? '16,185,129' : f.color === 0xf59e0b ? '245,158,11' : f.color === 0xa855f7 ? '168,85,247' : f.color === 0xf43f5e ? '244,63,94' : '6,182,212'},0.5)`;
                e.currentTarget.style.transform = 'translateY(-4px)';
                e.currentTarget.style.boxShadow = `0 16px 40px rgba(0,0,0,0.3)`;
                gsap.to(e.currentTarget, { y: -4, duration: 0.25, ease: 'power1.out' });
              }}
              onMouseLeave={e => {
                e.currentTarget.style.borderColor = 'rgba(35,41,56,0.9)';
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
                gsap.to(e.currentTarget, { y: 0, duration: 0.25, ease: 'power1.out' });
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16 }}>
                <div style={{
                  width: 44, height: 44, borderRadius: 10,
                  background: `rgba(${f.color === 0x3b82f6 ? '59,130,246' : f.color === 0x10b981 ? '16,185,129' : f.color === 0xf59e0b ? '245,158,11' : f.color === 0xa855f7 ? '168,85,247' : f.color === 0xf43f5e ? '244,63,94' : '6,182,212'},0.12)`,
                  border: `1px solid rgba(${f.color === 0x3b82f6 ? '59,130,246' : f.color === 0x10b981 ? '16,185,129' : f.color === 0xf59e0b ? '245,158,11' : f.color === 0xa855f7 ? '168,85,247' : f.color === 0xf43f5e ? '244,63,94' : '6,182,212'},0.25)`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center'
                }}>
                  {f.icon}
                </div>
                <h3 style={{ fontSize: 15, fontWeight: 600, letterSpacing: '-0.01em' }}>{f.title}</h3>
              </div>
              <p style={{ fontSize: 13, color: '#94a3b8', lineHeight: 1.65 }}>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ===== AGENT PIPELINE SECTION ===== */}
      <section id="pipeline" ref={agentsRef} style={{
        padding: '100px 48px',
        background: 'linear-gradient(180deg, rgba(12,13,18,1) 0%, rgba(15,18,26,1) 100%)',
        borderTop: '1px solid rgba(35,41,56,0.5)'
      }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 64 }}>
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              padding: '4px 12px', borderRadius: 20, marginBottom: 20,
              background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)',
              color: '#34d399', fontSize: 11, fontWeight: 600, letterSpacing: '0.07em', textTransform: 'uppercase'
            }}>
              Multi-Agent Architecture
            </div>
            <h2 style={{ fontSize: 'clamp(26px, 4vw, 44px)', fontWeight: 700, letterSpacing: '-0.03em', marginBottom: 16 }}>
              How the 6-Agent Pipeline Works
            </h2>
            <p style={{ fontSize: 16, color: '#9ca3af', maxWidth: 560, margin: '0 auto' }}>
              Each autonomous agent handles one specialized task in the trade audit flow —
              ensuring precision, traceability, and full compliance at every step.
            </p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {AGENTS.map((agent, i) => (
              <div key={i} className="hp-agent-step" style={{
                display: 'flex', gap: 24, padding: '24px 28px',
                borderRadius: 10, position: 'relative',
                background: 'rgba(18,21,29,0.6)',
                border: '1px solid rgba(35,41,56,0.7)',
                marginBottom: 8,
                transition: 'border-color 0.2s ease, background 0.2s ease',
                cursor: 'default'
              }}
                onMouseEnter={e => {
                  e.currentTarget.style.borderColor = agent.color;
                  e.currentTarget.style.background = 'rgba(24,28,39,0.9)';
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.borderColor = 'rgba(35,41,56,0.7)';
                  e.currentTarget.style.background = 'rgba(18,21,29,0.6)';
                }}
              >
                {/* Agent Number */}
                <div style={{
                  minWidth: 48, height: 48, borderRadius: 10,
                  background: `rgba(${agent.color.startsWith('#6') ? '96,165,250' : agent.color.startsWith('#3') ? '56,189,248' : agent.color.startsWith('#f5') ? '245,158,11' : agent.color.startsWith('#a') ? '168,85,247' : agent.color.startsWith('#1') ? '16,185,129' : '52,211,153'},0.12)`,
                  border: `1px solid ${agent.color}44`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontFamily: 'JetBrains Mono, monospace', fontWeight: 700,
                  fontSize: 15, color: agent.color
                }}>
                  {agent.num}
                </div>

                {/* Content */}
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                    <span style={{ fontSize: 15, fontWeight: 600 }}>{agent.name}</span>
                    <span style={{
                      fontSize: 10, padding: '2px 7px', borderRadius: 4,
                      background: `${agent.color}18`, border: `1px solid ${agent.color}33`,
                      color: agent.color, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em'
                    }}>
                      {agent.tag}
                    </span>
                  </div>
                  <p style={{ fontSize: 13, color: '#94a3b8', lineHeight: 1.6, margin: 0 }}>{agent.desc}</p>
                </div>

                {/* Connector arrow */}
                {i < AGENTS.length - 1 && (
                  <div style={{
                    position: 'absolute', bottom: -16, left: 48,
                    width: 1, height: 16,
                    background: 'linear-gradient(to bottom, rgba(59,130,246,0.4), transparent)',
                    zIndex: 1
                  }} />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== FINAL CTA SECTION ===== */}
      <section ref={ctaRef} style={{ padding: '100px 48px' }}>
        <div style={{
          maxWidth: 760, margin: '0 auto', textAlign: 'center',
          padding: '72px 48px', borderRadius: 20,
          background: 'linear-gradient(135deg, rgba(18,21,29,0.9) 0%, rgba(24,28,39,0.9) 100%)',
          border: '1px solid rgba(59,130,246,0.25)',
          boxShadow: '0 0 80px rgba(59,130,246,0.08), inset 0 1px 0 rgba(255,255,255,0.05)'
        }}>
          <div style={{
            width: 64, height: 64, borderRadius: 14,
            background: 'rgba(59,130,246,0.12)', border: '1px solid rgba(59,130,246,0.3)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 24px', color: '#60a5fa'
          }}>
            <TrendingUp size={28} />
          </div>
          <h2 style={{ fontSize: 'clamp(24px, 4vw, 40px)', fontWeight: 700, letterSpacing: '-0.03em', marginBottom: 16 }}>
            Ready to audit your first shipment?
          </h2>
          <p style={{ fontSize: 16, color: '#9ca3af', marginBottom: 36, lineHeight: 1.7 }}>
            Launch the audit platform — no setup required. Enter product, source, and destination to get a full landed cost analysis with compliance report in seconds.
          </p>
          <button
            onClick={() => navigate('/audit')}
            style={{
              padding: '16px 40px', borderRadius: 10, fontSize: 16, fontWeight: 700,
              background: '#f3f4f6', color: '#0c0d12', border: 'none', cursor: 'pointer',
              display: 'inline-flex', alignItems: 'center', gap: 10,
              boxShadow: '0 0 40px rgba(59,130,246,0.15)'
            }}
            onMouseEnter={e => { gsap.to(e.currentTarget, { scale: 1.04, duration: 0.2 }); }}
            onMouseLeave={e => { gsap.to(e.currentTarget, { scale: 1, duration: 0.2 }); }}
          >
            Open Audit Platform <ArrowRight size={18} />
          </button>
        </div>
      </section>

      {/* ===== FOOTER ===== */}
      <footer style={{
        borderTop: '1px solid rgba(35,41,56,0.6)',
        padding: '28px 48px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        flexWrap: 'wrap', gap: 16
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <ShieldCheck size={15} style={{ color: '#60a5fa' }} />
          <span style={{ fontSize: 13, color: '#64748b', fontWeight: 500 }}>LEXITAX AUDIT — Multi-Agent Trade Compliance</span>
        </div>
        <div style={{ fontSize: 12, color: '#475569' }}>
          AI Tax Auditor · Large Datasets · 40 Jurisdictions · 240 Policies
        </div>
      </footer>

      <style>{`
        @keyframes bounce {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(6px); }
        }
        body { overflow-x: hidden; }
      `}</style>
    </div>
  );
}
