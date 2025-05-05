import * as THREE from 'three';

class TouchControls {
    constructor(camera, domElement) {
        this.camera = camera;
        this.domElement = domElement;
        this.enabled = true;
        this.target = new THREE.Vector3();

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

export default TouchControls;