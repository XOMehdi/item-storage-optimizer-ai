import OrbitControls from './OrbitControls.js';
import TouchControls from './TouchControls.js';

// Get data from URL
const urlParams = new URLSearchParams(window.location.search);
let items = [];
let containerDimensions = [];
try {
    const containerParam = urlParams.get("container");
    const placementsParam = urlParams.get("placements");

    if (containerParam) {
        try {
            containerDimensions = JSON.parse(containerParam);
        } catch (e) {
            try {
                containerDimensions = JSON.parse(decodeURIComponent(containerParam));
            } catch (e2) {
                console.error("Failed to parse container after decoding", e2);
            }
        }
    }

    if (placementsParam) {
        try {
            items = JSON.parse(placementsParam);
        } catch (e) {
            try {
                items = JSON.parse(decodeURIComponent(placementsParam));
            } catch (e2) {
                console.error("Failed to parse placements after decoding", e2);
            }
        }
    }

    document.getElementById('itemCount').textContent = items.length;
} catch (e) {
    console.error("Failed to parse query params", e);
    document.getElementById('itemCount').textContent = "Error";
}

const containerWidth = containerDimensions[0];
const containerHeight = containerDimensions[1];
const containerDepth = containerDimensions[2];

// Initialize scene, camera, and renderer
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xf0f0f0);
const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(50, 50, 50);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

// Detect device type and set controls
const isMobile = /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
const controls = isMobile
    ? new TouchControls(camera, renderer.domElement)
    : new OrbitControls(camera, renderer.domElement);

controls.target = new THREE.Vector3(containerWidth / 2, containerHeight / 2, containerDepth / 2); // Center the view on the container
controls.update();

// Lighting
const light = new THREE.AmbientLight(0xffffff, 0.8);
scene.add(light);
const directional = new THREE.DirectionalLight(0xffffff, 0.8);
directional.position.set(10, 20, 10);
scene.add(directional);

// Container wireframe
const container = new THREE.BoxGeometry(containerWidth, containerHeight, containerDepth);
const wireframe = new THREE.EdgesGeometry(container);
const lineMaterial = new THREE.LineBasicMaterial({ color: 0x333333 });
const boxOutline = new THREE.LineSegments(wireframe, lineMaterial);
boxOutline.position.set(containerWidth / 2, containerHeight / 2, containerDepth / 2);
scene.add(boxOutline);

function getColorFromIndex(index) {
    const hue = (index * 137.508) % 360; // Golden angle approximation
    return new THREE.Color(`hsl(${hue}, 70%, 60%)`);
}


let meshes = [];

// Create box meshes
for (let i = 0; i < items.length; i++) {
    const item = items[i];
    if (!item || item.length < 7) continue; // Skip invalid items

    const [id, x, y, z, w, h, d] = item;
    const geometry = new THREE.BoxGeometry(w, h, d);

    const baseColor = getColorFromIndex(i);

    // Create canvas for ID label
    const canvas = document.createElement('canvas');
    canvas.width = 128;
    canvas.height = 128;
    const ctx = canvas.getContext('2d');

    // Draw label background
    ctx.fillStyle = baseColor.getStyle();
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw ID text
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 48px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(`#${id}`, canvas.width / 2, canvas.height / 2);

    const texture = new THREE.CanvasTexture(canvas);

    // Use same color for side faces, ID texture on top
    const materials = [
        new THREE.MeshStandardMaterial({ color: baseColor }), // right
        new THREE.MeshStandardMaterial({ color: baseColor }), // left
        new THREE.MeshStandardMaterial({ color: baseColor }), // top (will be replaced)
        new THREE.MeshStandardMaterial({ color: baseColor }), // bottom
        new THREE.MeshStandardMaterial({ color: baseColor }), // front
        new THREE.MeshStandardMaterial({ color: baseColor })  // back
    ];

    // Set ID texture on top and bottom faces
    materials[2] = new THREE.MeshStandardMaterial({ map: texture });
    materials[3] = new THREE.MeshStandardMaterial({ map: texture });

    const mesh = new THREE.Mesh(geometry, materials);
    mesh.position.set(x + w / 2, y + h / 2, z + d / 2);
    mesh.visible = false;
    scene.add(mesh);
    meshes.push(mesh);
}

// Animation controls
const speedRange = document.getElementById('speed-range');
let currentIndex = 0;
let isPlaying = false;
let interval;
let animationInterval = parseInt(speedRange.value);

function updateCounter() {
    document.getElementById('currentItem').textContent =
        currentIndex + " / " + meshes.length;
}

function play() {
    if (currentIndex >= meshes.length) return;

    if (isPlaying) {
        pause();
        return;
    }

    isPlaying = true;
    document.getElementById('play-pause-button').textContent = '▶️';
    document.getElementById('play-pause-button').style.backgroundColor = '#d4f7d4';
    interval = setInterval(() => {
        if (currentIndex < meshes.length) {
            meshes[currentIndex].visible = true;
            currentIndex++;
            updateCounter();
        } else {
            pause();
        }
    }, animationInterval);
}

function pause() {
    isPlaying = false;
    clearInterval(interval);
    document.getElementById('play-pause-button').textContent = '⏸️';
    document.getElementById('play-pause-button').style.backgroundColor = '';
}

function stepBack() {
    if (currentIndex <= 0) return;
    currentIndex--;
    meshes[currentIndex].visible = false;
    updateCounter();
    document.getElementById('stepback-button').style.backgroundColor = '#f0d4f0';
    setTimeout(() => {
        document.getElementById('stepback-button').style.backgroundColor = '';
    }, animationInterval);
}

function rewind() {
    pause();
    for (let mesh of meshes) mesh.visible = false;
    currentIndex = 0;
    updateCounter();
    document.getElementById('rewind-button').style.backgroundColor = '#d4d4f7';
    setTimeout(() => {
        document.getElementById('rewind-button').style.backgroundColor = '';
    }, animationInterval);
}

function calculateInterval(speed) {
    const minInterval = speedRange.min;
    const maxInterval = speedRange.max;

    // Ensure speed is within valid range (100 to 2000)
    speed = Math.max(speedRange.min, Math.min(speedRange.max, speed));

    // Linear interpolation: interval = maxInterval - (speed - minSpeed) * (maxInterval - minInterval) / (maxSpeed - minSpeed)
    const interval = maxInterval - ((speed - 100) * (maxInterval - minInterval) / (2000 - 100));

    // Round to nearest integer and ensure it's within bounds
    return Math.round(interval);
}

function changeSpeed() {
    let speed = parseInt(speedRange.value);
    document.getElementById('speed-label').textContent = `Speed: ${speed / 1000}x`;

    animationInterval = calculateInterval(speed);
    console.log(animationInterval);

    if (isPlaying) {
        clearInterval(interval); // Clear existing interval
        interval = setInterval(() => {
            if (currentIndex < meshes.length) {
                meshes[currentIndex].visible = true;
                currentIndex++;
                updateCounter();
            } else {
                pause();
            }
        }, animationInterval);
    }
}

function toggleHelpContent() {
    const helpContent = document.getElementById('help-content');
    helpContent.style.display = helpContent.style.display === 'block' ? 'none' : 'block';
}

function handleWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

speedRange.addEventListener('change', changeSpeed);
document.getElementById('play-pause-button').addEventListener('click', play);
document.getElementById('stepback-button').addEventListener('click', stepBack);
document.getElementById('rewind-button').addEventListener('click', rewind);
document.getElementById('help-button').addEventListener('click', toggleHelpContent);

// Initialize counter
updateCounter();

// Animation loop
function animate() {
    requestAnimationFrame(animate);
    renderer.render(scene, camera);
}
animate();

// Handle window resize
window.addEventListener('resize', handleWindowResize);

// Hide loading
setTimeout(() => {
    document.getElementById('loading').style.display = 'none';
}, 500);