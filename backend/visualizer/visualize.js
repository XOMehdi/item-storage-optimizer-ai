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

// Create colored materials for boxes
const colors = [
    0x3498db, // Blue
    0xe74c3c, // Red
    0x2ecc71, // Green
    0xf39c12, // Orange
    0x9b59b6, // Purple
    0x1abc9c, // Teal
    0xd35400, // Dark Orange
    0x34495e  // Dark Blue
];

let meshes = [];

// Create box meshes
for (let i = 0; i < items.length; i++) {
    const item = items[i];
    if (!item || item.length < 7) continue; // Skip invalid items

    const [id, x, y, z, w, h, d] = item;
    const geometry = new THREE.BoxGeometry(w, h, d);

    // Use a different color for each box
    const colorIndex = i % colors.length;
    const material = new THREE.MeshStandardMaterial({
        color: colors[colorIndex],
        transparent: true,
        opacity: 0.8
    });

    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(x + w / 2, y + h / 2, z + d / 2);
    mesh.visible = false;
    scene.add(mesh);
    meshes.push(mesh);
}

// Animation controls
let currentIndex = 0;
let isPlaying = false;
let interval;
const animationSpeed = 1000;

function updateCounter() {
    document.getElementById('currentItem').textContent =
        currentIndex + " / " + meshes.length;
}

function play() {
    if (isPlaying || currentIndex >= meshes.length) return;
    isPlaying = true;
    document.getElementById('play-button').style.backgroundColor = '#d4f7d4';
    document.getElementById('pause-button').style.backgroundColor = '';
    interval = setInterval(() => {
        if (currentIndex < meshes.length) {
            meshes[currentIndex].visible = true;
            currentIndex++;
            updateCounter();
        } else {
            pause();
        }
    }, 700);
}

function pause() {
    isPlaying = false;
    clearInterval(interval);
    document.getElementById('play-button').style.backgroundColor = '';
    document.getElementById('pause-button').style.backgroundColor = '#f7d4d4';
}

function rewind() {
    pause();
    for (let mesh of meshes) mesh.visible = false;
    currentIndex = 0;
    updateCounter();
    document.getElementById('pause-button').style.backgroundColor = '';
    document.getElementById('rewind-button').style.backgroundColor = '#d4d4f7';
    setTimeout(() => {
        document.getElementById('rewind-button').style.backgroundColor = '';
    }, 300);
}

// Buttons
document.getElementById('play-button').addEventListener('click', play);
document.getElementById('pause-button').addEventListener('click', pause);
document.getElementById('rewind-button').addEventListener('click', rewind);

// Help button
document.getElementById('help-button').addEventListener('click', function () {
    const helpContent = document.getElementById('help-content');
    helpContent.style.display = helpContent.style.display === 'block' ? 'none' : 'block';
});

// Initialize counter
updateCounter();

// Animation loop
function animate() {
    requestAnimationFrame(animate);
    renderer.render(scene, camera);
}
animate();

// Handle window resize
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

// Hide loading
setTimeout(() => {
    document.getElementById('loading').style.display = 'none';
}, 500);