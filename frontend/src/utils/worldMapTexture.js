import * as THREE from 'three';

// Equirectangular continent polygon paths: [longitude, latitude]
// X: -180 to 180, Y: -90 to 90
const CONTINENTS = [
  // North America
  [
    [-168, 65], [-162, 71], [-150, 71], [-130, 70], [-120, 76], [-95, 76], [-80, 70],
    [-65, 60], [-55, 50], [-60, 45], [-70, 42], [-75, 35], [-80, 25], [-82, 23],
    [-88, 21], [-88, 16], [-83, 10], [-77, 8], [-80, 8], [-85, 12], [-92, 16],
    [-97, 18], [-105, 20], [-110, 23], [-115, 30], [-124, 38], [-124, 48],
    [-130, 54], [-140, 60], [-150, 60], [-160, 55], [-166, 60], [-168, 65]
  ],
  // Greenland
  [
    [-45, 60], [-35, 65], [-20, 75], [-20, 82], [-35, 83], [-55, 82], [-60, 76],
    [-50, 70], [-45, 60]
  ],
  // South America
  [
    [-75, 10], [-60, 10], [-50, 0], [-35, -5], [-35, -10], [-38, -15], [-40, -22],
    [-50, -30], [-55, -35], [-65, -45], [-68, -55], [-75, -52], [-73, -40],
    [-70, -30], [-75, -20], [-80, -5], [-80, 2], [-75, 10]
  ],
  // Europe & Asia (Eurasia)
  [
    [-10, 36], [0, 38], [10, 38], [15, 40], [25, 35], [35, 32], [35, 37],
    [40, 40], [50, 30], [55, 25], [60, 25], [68, 22], [72, 18], [78, 8],
    [82, 12], [88, 22], [92, 20], [98, 10], [104, 2], [105, 10], [108, 15],
    [108, 22], [118, 24], [122, 30], [122, 38], [128, 38], [130, 42],
    [135, 45], [140, 50], [142, 55], [150, 60], [160, 60], [170, 65],
    [180, 65], [180, 72], [170, 72], [140, 74], [110, 76], [80, 74],
    [60, 70], [45, 68], [30, 70], [20, 70], [15, 65], [10, 58], [5, 54],
    [-5, 48], [-10, 44], [-10, 36]
  ],
  // Africa
  [
    [-5, 36], [10, 37], [25, 32], [32, 31], [35, 28], [42, 15], [50, 12],
    [45, 5], [40, -5], [35, -15], [32, -28], [28, -34], [18, -34], [15, -25],
    [12, -15], [10, 0], [2, 5], [-5, 5], [-15, 12], [-17, 15], [-17, 21],
    [-12, 28], [-5, 36]
  ],
  // Australia
  [
    [114, -22], [118, -34], [128, -32], [135, -35], [140, -37], [150, -36],
    [153, -28], [150, -22], [145, -15], [142, -11], [136, -12], [130, -14],
    [124, -16], [114, -22]
  ],
  // Great Britain & Ireland
  [
    [-5, 50], [-1, 51], [1, 53], [0, 57], [-3, 58], [-5, 55], [-5, 50]
  ],
  // Japan
  [
    [130, 32], [135, 34], [140, 36], [142, 42], [145, 44], [142, 45],
    [140, 40], [135, 36], [130, 32]
  ],
  // Madagascar
  [
    [44, -13], [50, -15], [48, -25], [44, -25], [44, -13]
  ],
  // New Zealand (North & South)
  [
    [167, -46], [172, -42], [176, -38], [174, -36], [173, -40], [168, -45], [167, -46]
  ],
  // Antarctica (base strip)
  [
    [-180, -75], [180, -75], [180, -90], [-180, -90], [-180, -75]
  ]
];

/**
 * Generates an equirectangular world map CanvasTexture
 * @param {boolean} isDark - Dark theme or Light theme
 * @returns {THREE.CanvasTexture}
 */
export function createWorldMapTexture(isDark = true) {
  const canvas = document.createElement('canvas');
  canvas.width = 2048;
  canvas.height = 1024;
  const ctx = canvas.getContext('2d');

  const w = canvas.width;
  const h = canvas.height;

  // Background Ocean Color
  ctx.fillStyle = isDark ? '#080c16' : '#e6edf5';
  ctx.fillRect(0, 0, w, h);

  // Draw Subtle Latitude & Longitude Meridian Grid Lines
  ctx.strokeStyle = isDark ? 'rgba(38, 52, 77, 0.4)' : 'rgba(180, 195, 215, 0.5)';
  ctx.lineWidth = 1;

  // Longitude lines (every 30 deg)
  for (let lng = -180; lng <= 180; lng += 30) {
    const x = ((lng + 180) / 360) * w;
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, h);
    ctx.stroke();
  }

  // Latitude lines (every 30 deg)
  for (let lat = -90; lat <= 90; lat += 30) {
    const y = ((90 - lat) / 180) * h;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(w, y);
    ctx.stroke();
  }

  // Equator Highlight
  ctx.strokeStyle = isDark ? 'rgba(59, 130, 246, 0.35)' : 'rgba(59, 130, 246, 0.3)';
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(0, h / 2);
  ctx.lineTo(w, h / 2);
  ctx.stroke();

  // Draw Continent Landmass Polygons
  ctx.fillStyle = isDark ? '#1a2436' : '#ffffff';
  ctx.strokeStyle = isDark ? '#2e3e5c' : '#94a3b8';
  ctx.lineWidth = 1.8;

  const latLngToCanvas = (lng, lat) => {
    const x = ((lng + 180) / 360) * w;
    const y = ((90 - lat) / 180) * h;
    return [x, y];
  };

  CONTINENTS.forEach(poly => {
    ctx.beginPath();
    poly.forEach((pt, idx) => {
      const [x, y] = latLngToCanvas(pt[0], pt[1]);
      if (idx === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
  });

  // Create Three.js Canvas Texture
  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.ClampToEdgeWrapping;
  texture.needsUpdate = true;
  return texture;
}
