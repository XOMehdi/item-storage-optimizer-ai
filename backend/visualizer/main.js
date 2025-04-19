// Make sure THREE is fully loaded before using it
document.addEventListener('DOMContentLoaded', function() {
    // OrbitControls implementation
    class OrbitControls {
    constructor(camera, domElement) {
        this.camera = camera;
        this.domElement = domElement;
        this.enabled = true;
        this.target = new THREE.Vector3();
        
        // Current position in spherical coordinates
        this.spherical = new THREE.Spherical();
        this.sphericalDelta = new THREE.Spherical();
        
        // Limits
        this.minDistance = 0;
        this.maxDistance = Infinity;
        
        // Mouse buttons
        this.mouseButtons = { LEFT: 0 }; // Changed from THREE.MOUSE.ROTATE
        
        // State
        this.isRotating = false;
        
        // Bind event handlers
        this.onMouseDown = this.onMouseDown.bind(this);
        this.onMouseMove = this.onMouseMove.bind(this);
        this.onMouseUp = this.onMouseUp.bind(this);
        this.onMouseWheel = this.onMouseWheel.bind(this);
        
        // Add event listeners
        this.domElement.addEventListener('mousedown', this.onMouseDown);
        this.domElement.addEventListener('mousemove', this.onMouseMove);
        this.domElement.addEventListener('mouseup', this.onMouseUp);
        this.domElement.addEventListener('wheel', this.onMouseWheel);
        
        this.update();
    }
    
    getZoomScale() {
        return 0.95;
    }
    
    rotateLeft(angle) {
        this.sphericalDelta.theta -= angle;
    }
    
    rotateUp(angle) {
        this.sphericalDelta.phi -= angle;
    }
    
    onMouseDown(event) {
        if (!this.enabled) return;
        
        if (event.button === 0) {
        this.isRotating = true;
        this.rotateStart = {
            x: event.clientX,
            y: event.clientY
        };
        }
    }
    
    onMouseMove(event) {
        if (!this.enabled || !this.isRotating) return;
        
        const element = this.domElement;
        const rotateEnd = {
        x: event.clientX,
        y: event.clientY
        };
        
        const rotateDelta = {
        x: rotateEnd.x - this.rotateStart.x,
        y: rotateEnd.y - this.rotateStart.y
        };
        
        // Rotating across the whole screen goes 360 degrees around
        this.rotateLeft(2 * Math.PI * rotateDelta.x / element.clientWidth);
        
        // Rotating up and down along the screen
        this.rotateUp(2 * Math.PI * rotateDelta.y / element.clientHeight);
        
        this.rotateStart = rotateEnd;
        
        this.update();
    }
    
    onMouseUp() {
        this.isRotating = false;
    }
    
    onMouseWheel(event) {
        if (!this.enabled) return;
        
        event.preventDefault();
        
        // Zoom in or out
        if (event.deltaY < 0) {
        this.dollyIn(this.getZoomScale());
        } else if (event.deltaY > 0) {
        this.dollyOut(this.getZoomScale());
        }
        
        this.update();
    }
    
    dollyIn(dollyScale) {
        this.spherical.radius /= dollyScale;
        this.spherical.radius = Math.max(this.minDistance, Math.min(this.maxDistance, this.spherical.radius));
    }
    
    dollyOut(dollyScale) {
        this.spherical.radius *= dollyScale;
        this.spherical.radius = Math.max(this.minDistance, Math.min(this.maxDistance, this.spherical.radius));
    }
    
    update() {
        const position = this.camera.position;
        const offset = position.clone().sub(this.target);
        
        // Convert to spherical coordinates
        this.spherical.setFromVector3(offset);
        
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
    document.body.appendChild(renderer.domElement);
    
    // Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target = new THREE.Vector3(20, 20, 20); // Center the view on the container
    controls.update();
    
    // Lighting
    const light = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(light);
    const directional = new THREE.DirectionalLight(0xffffff, 0.8);
    directional.position.set(10, 20, 10);
    scene.add(directional);
    
    // Container wireframe
    const container = new THREE.BoxGeometry(40, 40, 40);
    const wireframe = new THREE.EdgesGeometry(container);
    const lineMaterial = new THREE.LineBasicMaterial({ color: 0x333333 });
    const boxOutline = new THREE.LineSegments(wireframe, lineMaterial);
    boxOutline.position.set(20, 20, 20); // Center the container
    scene.add(boxOutline);
    
    // Get data from URL
    const urlParams = new URLSearchParams(window.location.search);
    let items = [];
    try {
    const dataParam = urlParams.get("data");
    if (dataParam) {
        // Try to parse as direct JSON
        try {
        items = JSON.parse(dataParam);
        } catch (e) {
        // If that fails, try to decode it first (for encoded URLs)
        items = JSON.parse(decodeURIComponent(dataParam));
        }
    }
    document.getElementById('itemCount').textContent = items.length;
    } catch (e) {
    console.error("Failed to parse query data", e);
    document.getElementById('itemCount').textContent = "Error parsing data";
    }
    
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
    if (item.length < 6) continue; // Skip invalid items
    
    const [x, y, z, w, h, d] = item;
    const geometry = new THREE.BoxGeometry(w, h, d);
    
    // Use a different color for each box
    const colorIndex = i % colors.length;
    const material = new THREE.MeshStandardMaterial({ 
        color: colors[colorIndex],
        transparent: true,
        opacity: 0.8
    });
    
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(x + w/2, y + h/2, z + d/2);
    mesh.visible = false;
    scene.add(mesh);
    meshes.push(mesh);
    }
    
    // Animation controls
    let currentIndex = 0;
    let isPlaying = false;
    let interval;
    
    function updateCounter() {
    document.getElementById('currentItem').textContent = 
        currentIndex + " / " + meshes.length;
    }
    
    window.play = function() {
    if (isPlaying || currentIndex >= meshes.length) return;
    isPlaying = true;
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
    
    window.pause = function() {
    isPlaying = false;
    clearInterval(interval);
    }
    
    window.rewind = function() {
    window.pause();
    for (let mesh of meshes) mesh.visible = false;
    currentIndex = 0;
    updateCounter();
    }
    
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
});