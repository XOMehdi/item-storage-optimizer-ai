import OrbitControls from './OrbitControls.js';
import TouchControls from './TouchControls.js';


// Initialize scene, camera, and renderer
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xf0f0f0);
const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(50, 50, 50);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);
document.body.appendChild(renderer.domElement);

// Detect device type and set controls
const isMobile = /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
const controls = isMobile
    ? new TouchControls(camera, renderer.domElement)
    : new OrbitControls(camera, renderer.domElement);

// Lighting
const light = new THREE.AmbientLight(0xffffff, 0.6);
scene.add(light);
const directional = new THREE.DirectionalLight(0xffffff, 0.8);
directional.position.set(20, 40, 30);
scene.add(directional);

// Get data from URL
const urlParams = new URLSearchParams(window.location.search);
let items = [];
let containerDimensions = [30, 20, 10]; // Default dimensions
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

// Container wireframe
const containerWidth = containerDimensions[0];
const containerHeight = containerDimensions[1];
const containerDepth = containerDimensions[2];

const container = new THREE.BoxGeometry(containerWidth, containerHeight, containerDepth);
const wireframe = new THREE.EdgesGeometry(container);
const lineMaterial = new THREE.LineBasicMaterial({ color: 0x333333 });
const boxOutline = new THREE.LineSegments(wireframe, lineMaterial);
boxOutline.position.set(containerWidth / 2, containerHeight / 2, containerDepth / 2);
scene.add(boxOutline);

// Colors
const colors = [0x3498db, 0xe74c3c, 0x2ecc71, 0xf39c12, 0x9b59b6, 0x1abc9c, 0xd35400, 0x34495e];

let meshes = [];
let labels = [];

// Utility to create ID labels
function createTextSprite(message) {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    const fontSize = 40;
    context.font = `${fontSize}px Arial`;
    context.fillStyle = 'black';
    context.fillText(message, 10, fontSize);

    const texture = new THREE.CanvasTexture(canvas);
    const spriteMaterial = new THREE.SpriteMaterial({ map: texture, transparent: true });
    const sprite = new THREE.Sprite(spriteMaterial);
    sprite.scale.set(10, 5, 1); // Adjust as needed
    return sprite;
}

// Create box meshes with labels
for (let i = 0; i < items.length; i++) {
    const item = items[i];
    if (!item || item.length < 7) continue;

    const [id, x, y, z, w, h, d] = item;
    const geometry = new THREE.BoxGeometry(w, h, d);
    const colorIndex = i % colors.length;
    const material = new THREE.MeshStandardMaterial({
        color: colors[colorIndex],
        transparent: true,
        opacity: 0.85
    });

    const containerPos = boxOutline.position;
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(
        containerPos.x + x + w / 2,
        containerPos.y + y + h / 2,
        containerPos.z + z + d / 2
    );
    mesh.visible = false;

    const label = createTextSprite(id.toString());
    label.position.set(
        mesh.position.x,
        mesh.position.y + h / 2 + 2,
        mesh.position.z
    );
    label.visible = false;

    scene.add(mesh);
    scene.add(label);

    meshes.push(mesh);
    labels.push(label);
}

// Animation controls
let currentIndex = 0;
let isPlaying = false;
let interval;
const animationSpeed = 300;

function updateCounter() {
    document.getElementById('currentItem').textContent = currentIndex + " / " + meshes.length;
}

function play() {
    if (isPlaying || currentIndex >= meshes.length) return;
    isPlaying = true;
    document.getElementById('play-button').style.backgroundColor = '#d4f7d4';
    document.getElementById('pause-button').style.backgroundColor = '';
    interval = setInterval(() => {
        if (currentIndex < meshes.length) {
            meshes[currentIndex].visible = true;
            labels[currentIndex].visible = true;
            currentIndex++;
            updateCounter();
        } else {
            pause();
        }
    }, animationSpeed);
}

function pause() {
    isPlaying = false;
    clearInterval(interval);
    document.getElementById('play-button').style.backgroundColor = '';
    document.getElementById('pause-button').style.backgroundColor = '#f7d4d4';
}

function rewind() {
    pause();
    for (let i = 0; i < meshes.length; i++) {
        meshes[i].visible = false;
        labels[i].visible = false;
    }
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

// Counter
updateCounter();

// Animation loop
function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
}
animate();

// Window resize
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

// Hide loading
setTimeout(() => {
    document.getElementById('loading').style.display = 'none';
}, 500);
