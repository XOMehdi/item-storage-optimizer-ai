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

export default OrbitControls;



for (let i = 0; i < items.length; i++) {
    const item = items[i];
    if (!item || item.length < 7) continue; // Skip invalid items

    const [id, x, y, z, w, h, d] = item;
    const geometry = new THREE.BoxGeometry(w, h, d);

    // Base color
    const colorIndex = i % colors.length;
    const baseColor = new THREE.Color(colors[colorIndex]);

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

    // Set ID texture on top face (index 2)
    materials[2] = new THREE.MeshStandardMaterial({ map: texture });

    const mesh = new THREE.Mesh(geometry, materials);
    mesh.position.set(x + w / 2, y + h / 2, z + d / 2);
    mesh.visible = false;
    scene.add(mesh);
    meshes.push(mesh);
}
