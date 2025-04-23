// Mobile Touch Controls Implementation
class TouchControls {
    constructor(camera, domElement) {
        this.camera = camera;
        this.domElement = domElement;
        this.enabled = true;
        this.target = new THREE.Vector3(20, 20, 20); // Center of the container

        // Current position in spherical coordinates
        this.spherical = new THREE.Spherical();
        this.sphericalDelta = new THREE.Spherical();

        // Pan settings
        this.panOffset = new THREE.Vector3();
        this.panSpeed = 0.3;

        // Zoom settings
        this.scale = 1;
        this.zoomSpeed = 0.1;
        this.minDistance = 10;
        this.maxDistance = 200;

        // State tracking
        this.isRotating = false;
        this.isPanning = false;
        this.isZooming = false;
        this.rotateStart = { x: 0, y: 0 };
        this.rotateEnd = { x: 0, y: 0 };
        this.panStart = { x: 0, y: 0 };
        this.panEnd = { x: 0, y: 0 };
        this.zoomDistStart = 0;

        // Bind event handlers
        this.onTouchStart = this.onTouchStart.bind(this);
        this.onTouchMove = this.onTouchMove.bind(this);
        this.onTouchEnd = this.onTouchEnd.bind(this);

        // Add event listeners
        this.domElement.addEventListener('touchstart', this.onTouchStart, false);
        this.domElement.addEventListener('touchmove', this.onTouchMove, false);
        this.domElement.addEventListener('touchend', this.onTouchEnd, false);

        // Initialize spherical coordinates
        this.updateSpherical();
    }

    updateSpherical() {
        const offset = this.camera.position.clone().sub(this.target);
        this.spherical.setFromVector3(offset);
    }

    onTouchStart(event) {
        if (!this.enabled) return;
        event.preventDefault();

        switch (event.touches.length) {
            case 1: // Single touch - rotate
                this.isRotating = true;
                this.rotateStart.x = event.touches[0].pageX;
                this.rotateStart.y = event.touches[0].pageY;
                break;

            case 2: // Two touches - pan or zoom
                const dx = event.touches[0].pageX - event.touches[1].pageX;
                const dy = event.touches[0].pageY - event.touches[1].pageY;
                this.zoomDistStart = Math.sqrt(dx * dx + dy * dy);

                // Set up for panning
                this.isPanning = true;
                this.panStart.x = (event.touches[0].pageX + event.touches[1].pageX) / 2;
                this.panStart.y = (event.touches[0].pageY + event.touches[1].pageY) / 2;

                // Also set up for zooming
                this.isZooming = true;
                break;
        }
    }

    onTouchMove(event) {
        if (!this.enabled) return;
        event.preventDefault();

        if (this.isRotating && event.touches.length === 1) {
            // Handle rotation
            this.rotateEnd.x = event.touches[0].pageX;
            this.rotateEnd.y = event.touches[0].pageY;

            // Calculate rotation
            const rotateDelta = {
                x: this.rotateEnd.x - this.rotateStart.x,
                y: this.rotateEnd.y - this.rotateStart.y
            };

            // Adjust rotation speed
            const rotateSpeed = 0.003;

            // Apply rotation
            this.sphericalDelta.theta -= rotateDelta.x * rotateSpeed;
            this.sphericalDelta.phi -= rotateDelta.y * rotateSpeed;

            // Update start position for next frame
            this.rotateStart.x = this.rotateEnd.x;
            this.rotateStart.y = this.rotateEnd.y;

            this.update();
        } else if (event.touches.length === 2) {
            // Handle zooming
            if (this.isZooming) {
                const dx = event.touches[0].pageX - event.touches[1].pageX;
                const dy = event.touches[0].pageY - event.touches[1].pageY;
                const distance = Math.sqrt(dx * dx + dy * dy);

                const ratio = distance / this.zoomDistStart;
                this.dolly(ratio);

                // Update the start distance for next frame
                this.zoomDistStart = distance;
            }

            // Handle panning
            if (this.isPanning) {
                this.panEnd.x = (event.touches[0].pageX + event.touches[1].pageX) / 2;
                this.panEnd.y = (event.touches[0].pageY + event.touches[1].pageY) / 2;

                const panDelta = {
                    x: this.panEnd.x - this.panStart.x,
                    y: this.panEnd.y - this.panStart.y
                };

                this.pan(panDelta.x, panDelta.y);

                // Update start position for next frame
                this.panStart.x = this.panEnd.x;
                this.panStart.y = this.panEnd.y;
            }

            this.update();
        }
    }

    onTouchEnd(event) {
        this.isRotating = false;
        this.isPanning = false;
        this.isZooming = false;
    }

    pan(deltaX, deltaY) {
        const offset = new THREE.Vector3();
        const element = this.domElement;

        // Calculate how far you're panning based on screen width/height
        offset.x = -2 * deltaX * this.panSpeed / element.clientWidth;
        offset.y = 2 * deltaY * this.panSpeed / element.clientHeight;

        // Apply to pan offset
        this.panOffset.add(offset);
    }

    dolly(dollyScale) {
        if (dollyScale > 1) {
            this.scale /= dollyScale;
        } else {
            this.scale *= 1 / dollyScale;
        }
    }

    update() {
        const position = this.camera.position;
        const offset = position.clone().sub(this.target);

        // Apply panning
        if (this.panOffset.lengthSq() > 0) {
            // Need to adjust pan direction based on current camera rotation
            const rotMatrix = new THREE.Matrix4().extractRotation(this.camera.matrix);
            const pan = new THREE.Vector3(this.panOffset.x, this.panOffset.y, 0);
            pan.applyMatrix4(rotMatrix);
            this.target.add(pan);
            position.add(pan);
            this.panOffset.set(0, 0, 0);
        }

        // Convert to spherical coordinates
        this.spherical.setFromVector3(offset);

        // Apply zoom
        if (this.scale !== 1) {
            this.spherical.radius /= this.scale;
            this.scale = 1;
        }

        // Clamp zoom distance
        this.spherical.radius = Math.max(this.minDistance, Math.min(this.maxDistance, this.spherical.radius));

        // Apply rotation
        this.spherical.theta += this.sphericalDelta.theta;
        this.spherical.phi += this.sphericalDelta.phi;

        // Restrict phi to between 0.1 and PI - 0.1
        this.spherical.phi = Math.max(0.1, Math.min(Math.PI - 0.1, this.spherical.phi));
        this.spherical.makeSafe();

        // Update position
        offset.setFromSpherical(this.spherical);
        position.copy(this.target).add(offset);

        this.camera.lookAt(this.target);

        // Reset deltas
        this.sphericalDelta.set(0, 0, 0);

        return true;
    }
}

// Initialize scene, camera, and renderer
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xf0f0f0);
const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(50, 50, 50);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);
document.body.appendChild(renderer.domElement);

// Controls
const controls = new TouchControls(camera, renderer.domElement);

// Lighting
const light = new THREE.AmbientLight(0xffffff, 0.6);
scene.add(light);
const directional = new THREE.DirectionalLight(0xffffff, 0.8);
directional.position.set(20, 40, 30);
scene.add(directional);

// Container wireframe
const container = new THREE.BoxGeometry(30, 20, 10);
const wireframe = new THREE.EdgesGeometry(container);
const lineMaterial = new THREE.LineBasicMaterial({ color: 0x333333 });
const boxOutline = new THREE.LineSegments(wireframe, lineMaterial);
boxOutline.position.set(20, 20, 20);
scene.add(boxOutline);

// Get data from URL
const urlParams = new URLSearchParams(window.location.search);
let items = [];
try {
    const dataParam = urlParams.get("data");
    if (dataParam) {
        try {
            items = JSON.parse(dataParam);
        } catch (e) {
            try {
                items = JSON.parse(decodeURIComponent(dataParam));
            } catch (e2) {
                console.error("Failed to parse data after decoding", e2);
            }
        }
    }
    document.getElementById('itemCount').textContent = items.length;
} catch (e) {
    console.error("Failed to parse query data", e);
    document.getElementById('itemCount').textContent = "Error";
}

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


    // Add container's position (20, 20, 20) as an offset
    const containerPos = boxOutline.position;
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(
        containerPos.x + x + w / 2, 
        containerPos.y + y + h / 2, 
        containerPos.z + z + d / 2
    );
    mesh.visible = false;

    // Also update the label position
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
