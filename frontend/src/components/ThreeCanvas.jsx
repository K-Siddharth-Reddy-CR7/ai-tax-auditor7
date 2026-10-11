import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as THREE from 'three';
import gsap from 'gsap';
import { Globe, GitMerge, RotateCw, ZoomIn, ZoomOut, Compass, Info, CheckCircle2 } from 'lucide-react';
import { createWorldMapTexture } from '../utils/worldMapTexture';

// 40 Trade Hubs with GPS Coordinates
const ALL_HUBS = {
  'India': { lat: 20.5937, lng: 78.9629, label: 'India (BOM/DEL)', duty: 10.0, vat: 18.0, cur: 'INR' },
  'United States': { lat: 37.0902, lng: -95.7129, label: 'USA (LAX/JFK)', duty: 3.5, vat: 0.0, cur: 'USD' },
  'Germany': { lat: 51.1657, lng: 10.4515, label: 'Germany (FRA/HAM)', duty: 4.2, vat: 19.0, cur: 'EUR' },
  'Japan': { lat: 36.2048, lng: 138.2529, label: 'Japan (HND/NRT)', duty: 2.8, vat: 10.0, cur: 'JPY' },
  'United Kingdom': { lat: 55.3781, lng: -3.4360, label: 'UK (LHR/FXT)', duty: 4.5, vat: 20.0, cur: 'GBP' },
  'China': { lat: 35.8617, lng: 104.1954, label: 'China (SHA/SZX)', duty: 7.5, vat: 13.0, cur: 'CNY' },
  'Singapore': { lat: 1.3521, lng: 103.8198, label: 'Singapore (SIN)', duty: 0.0, vat: 9.0, cur: 'SGD' },
  'Brazil': { lat: -14.2350, lng: -51.9253, label: 'Brazil (SSZ/GRU)', duty: 12.0, vat: 17.0, cur: 'BRL' },
  'Australia': { lat: -25.2744, lng: 133.7751, label: 'Australia (SYD)', duty: 5.0, vat: 10.0, cur: 'AUD' },
  'United Arab Emirates': { lat: 23.4241, lng: 53.8478, label: 'UAE (DXB/JEA)', duty: 5.0, vat: 5.0, cur: 'AED' },
  'Netherlands': { lat: 52.1326, lng: 5.2913, label: 'Netherlands (RTM)', duty: 4.2, vat: 21.0, cur: 'EUR' },
  'South Korea': { lat: 35.9078, lng: 127.7669, label: 'S. Korea (PUS)', duty: 8.0, vat: 10.0, cur: 'KRW' },
  'France': { lat: 46.2276, lng: 2.2137, label: 'France (CDG/MRS)', duty: 4.2, vat: 20.0, cur: 'EUR' },
  'Canada': { lat: 56.1304, lng: -106.3468, label: 'Canada (YVR/YYZ)', duty: 3.8, vat: 5.0, cur: 'CAD' },
  'Mexico': { lat: 23.6345, lng: -102.5528, label: 'Mexico (VER/MEX)', duty: 10.5, vat: 16.0, cur: 'MXN' },
  'Italy': { lat: 41.8719, lng: 12.5674, label: 'Italy (GOA/FCO)', duty: 4.2, vat: 22.0, cur: 'EUR' },
  'Spain': { lat: 40.4637, lng: -3.7492, label: 'Spain (BCN/VLC)', duty: 4.2, vat: 21.0, cur: 'EUR' },
  'Malaysia': { lat: 4.2105, lng: 101.9758, label: 'Malaysia (PKG)', duty: 6.0, vat: 10.0, cur: 'MYR' },
  'Thailand': { lat: 15.8700, lng: 100.9925, label: 'Thailand (BKK)', duty: 8.5, vat: 7.0, cur: 'THB' },
  'Saudi Arabia': { lat: 23.8859, lng: 45.0792, label: 'Saudi Arabia (JED)', duty: 5.5, vat: 15.0, cur: 'SAR' },
  'South Africa': { lat: -30.5595, lng: 22.9375, label: 'South Africa (DUR)', duty: 7.8, vat: 15.0, cur: 'ZAR' },
  'New Zealand': { lat: -40.9006, lng: 174.8860, label: 'New Zealand (AKL)', duty: 4.0, vat: 15.0, cur: 'NZD' },
  'Indonesia': { lat: -0.7893, lng: 113.9213, label: 'Indonesia (JKT)', duty: 7.5, vat: 11.0, cur: 'IDR' },
  'Vietnam': { lat: 14.0583, lng: 108.2772, label: 'Vietnam (SGN/HPH)', duty: 9.2, vat: 10.0, cur: 'VND' },
  'Philippines': { lat: 12.8797, lng: 121.7740, label: 'Philippines (MNL)', duty: 6.5, vat: 12.0, cur: 'PHP' },
  'Turkey': { lat: 38.9637, lng: 35.2433, label: 'Turkey (IST)', duty: 5.0, vat: 20.0, cur: 'TRY' },
  'Belgium': { lat: 50.5039, lng: 4.4699, label: 'Belgium (ANR)', duty: 4.2, vat: 21.0, cur: 'EUR' },
  'Sweden': { lat: 60.1282, lng: 18.6435, label: 'Sweden (GOT)', duty: 4.2, vat: 25.0, cur: 'SEK' },
  'Norway': { lat: 60.4720, lng: 8.4689, label: 'Norway (OSL)', duty: 4.5, vat: 25.0, cur: 'NOK' },
  'Denmark': { lat: 56.2639, lng: 9.5018, label: 'Denmark (CPH)', duty: 4.2, vat: 25.0, cur: 'DKK' },
  'Switzerland': { lat: 46.8182, lng: 8.2275, label: 'Switzerland (ZRH)', duty: 2.0, vat: 8.1, cur: 'CHF' },
  'Ireland': { lat: 53.1424, lng: -7.6921, label: 'Ireland (DUB)', duty: 4.2, vat: 23.0, cur: 'EUR' },
  'Portugal': { lat: 39.3999, lng: -8.2245, label: 'Portugal (LIS)', duty: 4.2, vat: 23.0, cur: 'EUR' },
  'Poland': { lat: 51.9194, lng: 19.1451, label: 'Poland (GDN)', duty: 4.2, vat: 23.0, cur: 'PLN' },
  'Austria': { lat: 47.5162, lng: 14.5501, label: 'Austria (VIE)', duty: 4.2, vat: 20.0, cur: 'EUR' },
  'Argentina': { lat: -38.4161, lng: -63.6167, label: 'Argentina (BUE)', duty: 14.0, vat: 21.0, cur: 'ARS' },
  'Chile': { lat: -35.6751, lng: -71.5430, label: 'Chile (VAP)', duty: 6.0, vat: 19.0, cur: 'CLP' },
  'Egypt': { lat: 26.8206, lng: 30.8025, label: 'Egypt (ALY)', duty: 10.0, vat: 14.0, cur: 'EGP' },
  'Nigeria': { lat: 9.0820, lng: 8.6753, label: 'Nigeria (LOS)', duty: 12.5, vat: 7.5, cur: 'NGN' },
  'Greece': { lat: 39.0742, lng: 21.8243, label: 'Greece (PIR)', duty: 4.2, vat: 24.0, cur: 'EUR' }
};

// The 6 Cognitive Multi-Agent Definitions with Clear Descriptions
const AGENT_SPECIFICATIONS = [
  {
    step: 1,
    id: 'input',
    name: '1. INPUT AGENT',
    tag: 'Sanitization & Validation',
    desc: 'Normalizes product specs, quantities, declared unit value & CIF shipping freight terms.',
    color: '#60a5fa'
  },
  {
    step: 2,
    id: 'product',
    name: '2. PRODUCT AGENT',
    tag: 'HS-6 Classification',
    desc: 'Fuzzy-matches commercial description against 1,200 catalog commodities to assign standard HS Code.',
    color: '#38bdf8'
  },
  {
    step: 3,
    id: 'rag',
    name: '3. RAG POLICY AGENT',
    tag: 'Vector Regulatory Search',
    desc: 'Executes dense TF-IDF vector retrieval over 240 compliance rules, flagging BIS, CE, and FDA permits.',
    color: '#f59e0b'
  },
  {
    step: 4,
    id: 'tax',
    name: '4. TAX AGENT',
    tag: 'Tariff Schedule Match',
    desc: 'Matches statutory import duty percentages, national GST/VAT rates, and local currency schedules.',
    color: '#a855f7'
  },
  {
    step: 5,
    id: 'calc',
    name: '5. CALCULATION AGENT',
    tag: 'Customs Valuation Engine',
    desc: 'Computes assessable customs value, exact duty amount, taxable base, statutory VAT, and landed cost.',
    color: '#10b981'
  },
  {
    step: 6,
    id: 'report',
    name: '6. REPORT AGENT',
    tag: 'Provenance & Verdict',
    desc: 'Compiles full audit provenance trace, assigns cryptographic audit ID, and outputs compliance verdict.',
    color: '#34d399'
  }
];

function latLngToVector3(lat, lng, radius) {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lng + 180) * (Math.PI / 180);
  const x = -(radius * Math.sin(phi) * Math.cos(theta));
  const z = radius * Math.sin(phi) * Math.sin(theta);
  const y = radius * Math.cos(phi);
  return new THREE.Vector3(x, y, z);
}

export default function ThreeCanvas({
  sourceCountry = 'United States',
  activeDestination = 'India',
  activeProduct = 'Laptop',
  isAuditing = false,
  isDark = true,
  onSelectHub
}) {
  const mountRef = useRef(null);
  const [viewMode, setViewMode] = useState('globe'); // 'globe' | 'pipeline'
  const [autoRotate, setAutoRotate] = useState(true);
  const [hoveredHub, setHoveredHub] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  const [selectedAgent, setSelectedAgent] = useState(AGENT_SPECIFICATIONS[0]);

  const sceneStateRef = useRef({
    scene: null,
    camera: null,
    renderer: null,
    globeGroup: null,
    pipelineGroup: null,
    globeMesh: null,
    hubMarkers: [],
    tradeArc: null,
    pulseParticles: [],
    pipePulse: null,
    pipeCurve: null,
    pipeProgress: 0,
    raycaster: new THREE.Raycaster(),
    mouse: new THREE.Vector2(-1000, -1000),
    animId: null,
    isDragging: false,
    prevMouse: { x: 0, y: 0 },
    targetRotation: { x: 0.2, y: 0 },
    currentRotation: { x: 0.2, y: 0 },
    zoom: 260,
    radius: 80,
    isHoveredOnMarker: false
  });

  // Focus smooth camera on country
  const focusOnCountry = useCallback((countryName) => {
    const hub = ALL_HUBS[countryName];
    if (!hub) return;
    const s = sceneStateRef.current;
    if (!s.globeGroup) return;

    const targetY = -(hub.lng + 90) * (Math.PI / 180);
    const targetX = (hub.lat) * (Math.PI / 180) * 0.45;

    gsap.to(s.targetRotation, {
      x: targetX,
      y: targetY,
      duration: 1.2,
      ease: 'power3.out'
    });
  }, []);

  // When source or destination changes, focus
  useEffect(() => {
    if (activeDestination && ALL_HUBS[activeDestination]) {
      focusOnCountry(activeDestination);
    }
  }, [activeDestination, focusOnCountry]);

  // Main Three.js Scene Setup
  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const width = container.clientWidth || 800;
    const height = container.clientHeight || 580;

    // Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(isDark ? 0x080a10 : 0xf1f5f9);

    // Camera
    const camera = new THREE.PerspectiveCamera(45, width / height, 1, 1400);
    camera.position.z = 260;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, isDark ? 0.9 : 1.1);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0xffffff, isDark ? 1.4 : 1.2);
    dirLight1.position.set(120, 100, 160);
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0x3b82f6, isDark ? 0.6 : 0.4);
    dirLight2.position.set(-120, -80, -100);
    scene.add(dirLight2);

    // --- 1. GLOBE WITH REAL GEOGRAPHICAL MAP ---
    const globeGroup = new THREE.Group();
    scene.add(globeGroup);

    const radius = 80;

    // Create World Map Texture using Equirectangular Continent Canvas
    const worldTexture = createWorldMapTexture(isDark);

    // Sphere with geographical texture
    const globeGeo = new THREE.SphereGeometry(radius, 64, 64);
    const globeMat = new THREE.MeshStandardMaterial({
      map: worldTexture,
      roughness: 0.55,
      metalness: 0.1
    });
    const globeMesh = new THREE.Mesh(globeGeo, globeMat);
    globeGroup.add(globeMesh);

    // Subtle Outer Atmosphere Ring
    const atmosGeo = new THREE.SphereGeometry(radius + 1.2, 48, 48);
    const atmosMat = new THREE.MeshBasicMaterial({
      color: isDark ? 0x1d293d : 0x94a3b8,
      transparent: true,
      opacity: isDark ? 0.15 : 0.08,
      side: THREE.BackSide
    });
    const atmosMesh = new THREE.Mesh(atmosGeo, atmosMat);
    globeGroup.add(atmosMesh);

    // Hub markers for all 40 countries
    const hubMarkers = [];
    const srcHub = ALL_HUBS[sourceCountry] || ALL_HUBS['United States'];
    const destHub = ALL_HUBS[activeDestination] || ALL_HUBS['India'];

    const srcVec = latLngToVector3(srcHub.lat, srcHub.lng, radius);
    const destVec = latLngToVector3(destHub.lat, destHub.lng, radius);

    Object.entries(ALL_HUBS).forEach(([name, hub]) => {
      const vec = latLngToVector3(hub.lat, hub.lng, radius);
      const isSrc = name === sourceCountry;
      const isDest = name === activeDestination;

      const markerGeo = new THREE.SphereGeometry(isSrc || isDest ? 2.5 : 1.4, 16, 16);
      const markerMat = new THREE.MeshStandardMaterial({
        color: isDest ? 0x10b981 : (isSrc ? 0x3b82f6 : (isDark ? 0x64748b : 0x94a3b8)),
        emissive: isDest ? 0x059669 : (isSrc ? 0x1d4ed8 : 0x000000),
        emissiveIntensity: isDest || isSrc ? 1.0 : 0.0,
        roughness: 0.2
      });
      const marker = new THREE.Mesh(markerGeo, markerMat);
      marker.position.copy(vec);
      marker.userData = { countryName: name, hubData: hub, isSrc, isDest };
      globeGroup.add(marker);
      hubMarkers.push(marker);

      // Add concentric pulse ring for active source & destination
      if (isSrc || isDest) {
        const ringGeo = new THREE.RingGeometry(2.0, 3.2, 24);
        const ringMat = new THREE.MeshBasicMaterial({
          color: isDest ? 0x10b981 : 0x3b82f6,
          side: THREE.DoubleSide,
          transparent: true,
          opacity: 0.85
        });
        const ringMesh = new THREE.Mesh(ringGeo, ringMat);
        ringMesh.position.copy(vec);
        ringMesh.lookAt(new THREE.Vector3(0, 0, 0));
        globeGroup.add(ringMesh);
      }
    });

    // 3D Trade Arc between Source and Destination
    const mid = srcVec.clone().add(destVec).multiplyScalar(0.5);
    const dist = srcVec.distanceTo(destVec);
    mid.normalize().multiplyScalar(radius + Math.max(20, dist * 0.28));

    const arcCurve = new THREE.QuadraticBezierCurve3(srcVec, mid, destVec);
    const arcPoints = arcCurve.getPoints(60);
    const arcGeo = new THREE.BufferGeometry().setFromPoints(arcPoints);
    const arcMat = new THREE.LineBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.9,
      linewidth: 2
    });
    const tradeArc = new THREE.Line(arcGeo, arcMat);
    globeGroup.add(tradeArc);

    // Pulse cargo particles traveling along trade arc
    const pulseParticles = [];
    for (let i = 0; i < 3; i++) {
      const pulseGeo = new THREE.SphereGeometry(1.4, 10, 10);
      const pulseMat = new THREE.MeshBasicMaterial({ color: 0x34d399 });
      const pulseMesh = new THREE.Mesh(pulseGeo, pulseMat);
      globeGroup.add(pulseMesh);
      pulseParticles.push({
        mesh: pulseMesh,
        curve: arcCurve,
        progress: (i * 0.33) % 1,
        speed: 0.007
      });
    }

    // --- 2. CLEAR & DESCRIPTIVE 3D MULTI-AGENT PIPELINE ---
    const pipelineGroup = new THREE.Group();
    pipelineGroup.visible = false;
    scene.add(pipelineGroup);

    const pipePositions = [
      new THREE.Vector3(-110, 0, 0),
      new THREE.Vector3(-66, 24, 15),
      new THREE.Vector3(-22, -24, -10),
      new THREE.Vector3(22, 24, 15),
      new THREE.Vector3(66, -24, -10),
      new THREE.Vector3(110, 0, 0)
    ];

    const agentMeshes = [];
    AGENT_SPECIFICATIONS.forEach((agent, i) => {
      const pos = pipePositions[i];

      // Outer Card Box
      const boxGeo = new THREE.BoxGeometry(20, 12, 8);
      const boxMat = new THREE.MeshStandardMaterial({
        color: isDark ? 0x141824 : 0xffffff,
        roughness: 0.3,
        metalness: 0.6
      });
      const boxMesh = new THREE.Mesh(boxGeo, boxMat);
      boxMesh.position.copy(pos);
      boxMesh.userData = { agentData: agent };
      pipelineGroup.add(boxMesh);
      agentMeshes.push(boxMesh);

      // Wireframe border
      const wireGeo = new THREE.BoxGeometry(20.3, 12.3, 8.3);
      const wireMat = new THREE.MeshBasicMaterial({
        color: new THREE.Color(agent.color),
        wireframe: true
      });
      const wireMesh = new THREE.Mesh(wireGeo, wireMat);
      wireMesh.position.copy(pos);
      pipelineGroup.add(wireMesh);
    });

    // Pipeline connecting line
    const pipeCurve = new THREE.CatmullRomCurve3(pipePositions);
    const pipePoints = pipeCurve.getPoints(100);
    const pipeLineGeo = new THREE.BufferGeometry().setFromPoints(pipePoints);
    const pipeLineMat = new THREE.LineBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.75,
      linewidth: 2
    });
    const pipeLine = new THREE.Line(pipeLineGeo, pipeLineMat);
    pipelineGroup.add(pipeLine);

    // Moving pulse along pipeline
    const pipePulseGeo = new THREE.SphereGeometry(2.4, 12, 12);
    const pipePulseMat = new THREE.MeshBasicMaterial({ color: 0x10b981 });
    const pipePulse = new THREE.Mesh(pipePulseGeo, pipePulseMat);
    pipelineGroup.add(pipePulse);

    // Save refs
    sceneStateRef.current = {
      ...sceneStateRef.current,
      scene,
      camera,
      renderer,
      globeGroup,
      pipelineGroup,
      globeMesh,
      hubMarkers,
      agentMeshes,
      tradeArc,
      pulseParticles,
      pipePulse,
      pipeCurve,
      pipeProgress: 0,
      radius
    };

    // GSAP camera entrance
    gsap.from(camera.position, {
      z: 360,
      duration: 1.4,
      ease: 'power3.out'
    });

    // Animation Loop
    const animate = () => {
      const s = sceneStateRef.current;
      if (!s.renderer) return;

      if (viewMode === 'globe' && s.globeGroup) {
        if (autoRotate && !s.isDragging && !s.isHoveredOnMarker) {
          s.targetRotation.y += 0.0022;
        }

        s.currentRotation.y += (s.targetRotation.y - s.currentRotation.y) * 0.08;
        s.currentRotation.x += (s.targetRotation.x - s.currentRotation.x) * 0.08;

        s.globeGroup.rotation.y = s.currentRotation.y;
        s.globeGroup.rotation.x = s.currentRotation.x;

        s.pulseParticles.forEach(p => {
          p.progress = (p.progress + p.speed) % 1;
          const pos = p.curve.getPoint(p.progress);
          p.mesh.position.copy(pos);
        });
      }

      if (viewMode === 'pipeline' && s.pipelineGroup && s.pipePulse && s.pipeCurve) {
        s.pipeProgress = (s.pipeProgress + 0.0065) % 1;
        const pt = s.pipeCurve.getPoint(s.pipeProgress);
        s.pipePulse.position.copy(pt);
        s.pipelineGroup.rotation.y += 0.0018;
      }

      s.renderer.render(s.scene, s.camera);
      s.animId = requestAnimationFrame(animate);
    };

    animate();

    // Pointer Interaction & Raycasting
    let lastHovered = null;

    const handlePointerMove = (e) => {
      const rect = container.getBoundingClientRect();
      const s = sceneStateRef.current;

      const clientX = e.clientX || (e.touches && e.touches[0].clientX);
      const clientY = e.clientY || (e.touches && e.touches[0].clientY);

      if (s.isDragging) {
        const deltaX = clientX - s.prevMouse.x;
        const deltaY = clientY - s.prevMouse.y;
        s.targetRotation.y += deltaX * 0.005;
        s.targetRotation.x += deltaY * 0.005;
        s.targetRotation.x = Math.max(-Math.PI / 3, Math.min(Math.PI / 3, s.targetRotation.x));
        s.prevMouse = { x: clientX, y: clientY };
        return;
      }

      if (!clientX || !clientY) return;

      const x = ((clientX - rect.left) / rect.width) * 2 - 1;
      const y = -((clientY - rect.top) / rect.height) * 2 + 1;
      s.mouse.set(x, y);

      if (viewMode === 'globe') {
        s.raycaster.setFromCamera(s.mouse, s.camera);
        const intersects = s.raycaster.intersectObjects(s.hubMarkers);

        if (intersects.length > 0) {
          const hit = intersects[0].object;
          s.isHoveredOnMarker = true;
          container.style.cursor = 'pointer';

          if (lastHovered !== hit) {
            if (lastHovered) gsap.to(lastHovered.scale, { x: 1, y: 1, z: 1, duration: 0.2 });
            lastHovered = hit;
            gsap.to(hit.scale, { x: 1.7, y: 1.7, z: 1.7, duration: 0.25, ease: 'back.out(2)' });
            setHoveredHub(hit.userData.hubData);
          }
          setTooltipPos({ x: clientX - rect.left + 15, y: clientY - rect.top - 15 });
        } else {
          s.isHoveredOnMarker = false;
          container.style.cursor = 'grab';
          if (lastHovered) {
            gsap.to(lastHovered.scale, { x: 1, y: 1, z: 1, duration: 0.2 });
            lastHovered = null;
            setHoveredHub(null);
          }
        }
      } else if (viewMode === 'pipeline' && s.agentMeshes) {
        s.raycaster.setFromCamera(s.mouse, s.camera);
        const intersects = s.raycaster.intersectObjects(s.agentMeshes);
        if (intersects.length > 0) {
          const hit = intersects[0].object;
          container.style.cursor = 'pointer';
          setSelectedAgent(hit.userData.agentData);
        } else {
          container.style.cursor = 'default';
        }
      }
    };

    const handlePointerDown = (e) => {
      const s = sceneStateRef.current;
      const clientX = e.clientX || (e.touches && e.touches[0].clientX);
      const clientY = e.clientY || (e.touches && e.touches[0].clientY);
      s.isDragging = true;
      s.prevMouse = { x: clientX, y: clientY };
      container.style.cursor = 'grabbing';
    };

    const handlePointerUp = () => {
      const s = sceneStateRef.current;
      s.isDragging = false;
      container.style.cursor = 'grab';

      if (viewMode === 'globe') {
        s.raycaster.setFromCamera(s.mouse, s.camera);
        const intersects = s.raycaster.intersectObjects(s.hubMarkers);
        if (intersects.length > 0) {
          const hit = intersects[0].object;
          const country = hit.userData.countryName;
          if (country) {
            focusOnCountry(country);
            if (onSelectHub) onSelectHub(country);
          }
        }
      }
    };

    const handleWheel = (e) => {
      e.preventDefault();
      const s = sceneStateRef.current;
      s.zoom = Math.max(140, Math.min(380, s.zoom + e.deltaY * 0.18));
      gsap.to(s.camera.position, { z: s.zoom, duration: 0.3, ease: 'power1.out' });
    };

    const resizeObserver = new ResizeObserver((entries) => {
      for (let entry of entries) {
        const { width: newWidth, height: newHeight } = entry.contentRect;
        const s = sceneStateRef.current;
        if (s.renderer && s.camera && newWidth > 0 && newHeight > 0) {
          s.camera.aspect = newWidth / newHeight;
          s.camera.updateProjectionMatrix();
          s.renderer.setSize(newWidth, newHeight);
        }
      }
    });

    resizeObserver.observe(container);

    container.addEventListener('pointermove', handlePointerMove);
    container.addEventListener('pointerdown', handlePointerDown);
    window.addEventListener('pointerup', handlePointerUp);
    container.addEventListener('wheel', handleWheel, { passive: false });

    return () => {
      cancelAnimationFrame(sceneStateRef.current.animId);
      resizeObserver.disconnect();
      container.removeEventListener('pointermove', handlePointerMove);
      container.removeEventListener('pointerdown', handlePointerDown);
      window.removeEventListener('pointerup', handlePointerUp);
      container.removeEventListener('wheel', handleWheel);
      renderer.dispose();
    };
  }, [sourceCountry, activeDestination, isDark, focusOnCountry, onSelectHub]);

  // Mode change with GSAP transition
  const handleModeChange = (mode) => {
    setViewMode(mode);
    const s = sceneStateRef.current;
    if (s.globeGroup && s.pipelineGroup) {
      if (mode === 'globe') {
        s.pipelineGroup.visible = false;
        s.globeGroup.visible = true;
        gsap.fromTo(s.globeGroup.scale, { x: 0.85, y: 0.85, z: 0.85 }, { x: 1, y: 1, z: 1, duration: 0.5, ease: 'power2.out' });
      } else {
        s.globeGroup.visible = false;
        s.pipelineGroup.visible = true;
        gsap.fromTo(s.pipelineGroup.scale, { x: 0.85, y: 0.85, z: 0.85 }, { x: 1, y: 1, z: 1, duration: 0.5, ease: 'power2.out' });
      }
    }
  };

  const handleZoomChange = (delta) => {
    const s = sceneStateRef.current;
    if (!s.camera) return;
    s.zoom = Math.max(140, Math.min(380, s.zoom + delta));
    gsap.to(s.camera.position, { z: s.zoom, duration: 0.35, ease: 'power2.out' });
  };

  const handleResetView = () => {
    const s = sceneStateRef.current;
    gsap.to(s.targetRotation, { x: 0.2, y: 0, duration: 1.1, ease: 'power3.out' });
    gsap.to(s.camera.position, { z: 260, duration: 1.1, ease: 'power3.out' });
    s.zoom = 260;
  };

  return (
    <div className="three-viewport" style={{ position: 'relative' }}>
      {/* Top Controls Overlay */}
      <div className="three-overlay">
        <button
          className={`btn-secondary ${viewMode === 'globe' ? 'active' : ''}`}
          onClick={() => handleModeChange('globe')}
        >
          <Globe size={13} />
          Geographical Trade Globe
        </button>
        <button
          className={`btn-secondary ${viewMode === 'pipeline' ? 'active' : ''}`}
          onClick={() => handleModeChange('pipeline')}
        >
          <GitMerge size={13} />
          3D Multi-Agent Pipeline
        </button>
        <button
          className="btn-secondary"
          onClick={() => setAutoRotate(!autoRotate)}
          title="Toggle Auto-Rotation"
        >
          <RotateCw size={13} className={autoRotate ? 'spin' : ''} />
          {autoRotate ? 'Rotation On' : 'Paused'}
        </button>
        <button className="btn-secondary" onClick={() => handleZoomChange(-35)} title="Zoom In">
          <ZoomIn size={13} />
        </button>
        <button className="btn-secondary" onClick={() => handleZoomChange(35)} title="Zoom Out">
          <ZoomOut size={13} />
        </button>
        <button className="btn-secondary" onClick={handleResetView} title="Reset Orientation">
          <Compass size={13} />
        </button>
      </div>

      {/* 3D WebGL Canvas */}
      <div ref={mountRef} style={{ width: '100%', height: '100%' }} />

      {/* Raycaster Tooltip on Globe Hover */}
      {hoveredHub && viewMode === 'globe' && (
        <div
          style={{
            position: 'absolute',
            left: tooltipPos.x,
            top: tooltipPos.y,
            pointerEvents: 'none',
            zIndex: 30,
            backgroundColor: 'var(--bg-card)',
            border: '1px solid var(--border-focus)',
            borderRadius: 6,
            padding: '8px 12px',
            fontSize: 12,
            boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
            transform: 'translateY(-50%)',
            backdropFilter: 'blur(8px)'
          }}
        >
          <div style={{ fontWeight: 600, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ color: '#10b981' }}>●</span>
            {hoveredHub.label}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'auto auto', gap: '2px 10px', marginTop: 4, color: 'var(--text-muted)', fontSize: 11 }}>
            <span>Statutory Tariff:</span>
            <span className="mono" style={{ color: '#f59e0b', textAlign: 'right' }}>{hoveredHub.duty}%</span>
            <span>VAT / GST:</span>
            <span className="mono" style={{ color: '#3b82f6', textAlign: 'right' }}>{hoveredHub.vat}%</span>
            <span>Currency:</span>
            <span className="mono" style={{ color: 'var(--text-main)', textAlign: 'right' }}>{hoveredHub.cur}</span>
          </div>
          <div style={{ fontSize: 10, color: 'var(--text-dim)', marginTop: 4, borderTop: '1px solid var(--border)', paddingTop: 3 }}>
            Click node to focus & select destination
          </div>
        </div>
      )}

      {/* Clear Descriptive Agent Inspector Overlay in Pipeline Mode */}
      {viewMode === 'pipeline' && (
        <div style={{
          position: 'absolute',
          bottom: 16,
          right: 16,
          maxWidth: 380,
          backgroundColor: 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderRadius: 8,
          padding: 16,
          zIndex: 20,
          boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
          backdropFilter: 'blur(8px)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
            <span className="mono" style={{ fontSize: 11, color: selectedAgent.color, fontWeight: 600 }}>
              {selectedAgent.name}
            </span>
            <span className="badge badge-success">
              <CheckCircle2 size={11} />
              ACTIVE
            </span>
          </div>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-main)', marginBottom: 4 }}>
            {selectedAgent.tag}
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.5 }}>
            {selectedAgent.desc}
          </div>
          <div style={{ display: 'flex', gap: 4, marginTop: 12, borderTop: '1px solid var(--border)', paddingTop: 8 }}>
            {AGENT_SPECIFICATIONS.map(a => (
              <button
                key={a.step}
                className="mono"
                style={{
                  flex: 1,
                  padding: '3px 0',
                  fontSize: 10,
                  borderRadius: 4,
                  border: '1px solid',
                  borderColor: selectedAgent.step === a.step ? a.color : 'var(--border)',
                  background: selectedAgent.step === a.step ? a.color : 'transparent',
                  color: selectedAgent.step === a.step ? '#fff' : 'var(--text-muted)',
                  cursor: 'pointer'
                }}
                onClick={() => setSelectedAgent(a)}
              >
                {a.step}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Bottom Telemetry HUD */}
      <div className="three-hud">
        <div className="three-hud-title">
          {viewMode === 'globe' ? 'ACTIVE GEOGRAPHICAL TRADE CORRIDOR' : 'COGNITIVE MULTI-AGENT SPECIFICATION'}
        </div>
        {viewMode === 'globe' ? (
          <div>
            Route: <span className="mono" style={{ color: '#3b82f6' }}>{sourceCountry}</span> &rarr;{' '}
            <span className="mono" style={{ color: '#10b981' }}>{activeDestination}</span>
            <div style={{ marginTop: 4, fontSize: '11px', color: 'var(--text-dim)' }}>
              Geographical continent map with real customs ports. Drag to rotate, scroll to zoom.
            </div>
          </div>
        ) : (
          <div>
            Pipeline Status: <span className="mono" style={{ color: '#10b981' }}>{isAuditing ? 'PROCESSING_TRADE' : 'READY_STANDBY'}</span>
            <div style={{ marginTop: 4, fontSize: '11px', color: 'var(--text-dim)' }}>
              6 specialized agents sequentially auditing valuation, tariff schedules & RAG policy compliance. Click any agent number above to inspect.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
