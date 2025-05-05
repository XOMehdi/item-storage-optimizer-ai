import * as THREE from 'three';
import Config from '../core/Config.js';
import OrbitControls from "../controls/OrbitControls.js";
import TouchControls from "../controls/TouchControls.js";

class SceneManager {
    constructor(container) {
        this.container = container;
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
        this.renderer = null;

        this.initialize();
    }

    initialize() {
        // Setup scene
        this.scene.background = new THREE.Color(Config.COLORS.BACKGROUND);

        // Setup camera
        this.camera.position.set(50, 50, 50);

        // Setup renderer
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        document.body.appendChild(this.renderer.domElement);

        // Setup controls
        this.setupControls();

        // Setup lighting
        this.setupLighting();

        // Create container outline
        this.createContainerOutline();

        // Handle window resize
        window.addEventListener('resize', () => this.handleResize());
    }

    setupControls() {
        const isMobile = /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        this.controls = isMobile
            ? new TouchControls(this.camera, this.renderer.domElement)
            : new OrbitControls(this.camera, this.renderer.domElement);

        this.controls.target = new THREE.Vector3(
            this.container.width / 2,
            this.container.height / 2,
            this.container.depth / 2
        );
        this.controls.update();
    }

    setupLighting() {
        const ambient = new THREE.AmbientLight(0xffffff, 0.8);
        this.scene.add(ambient);

        const directional = new THREE.DirectionalLight(0xffffff, 0.8);
        directional.position.set(10, 20, 10);
        this.scene.add(directional);
    }

    createContainerOutline() {
        const container = new THREE.BoxGeometry(
            this.container.width,
            this.container.height,
            this.container.depth
        );
        const wireframe = new THREE.EdgesGeometry(container);
        const lineMaterial = new THREE.LineBasicMaterial({ color: Config.COLORS.CONTAINER_OUTLINE });
        const boxOutline = new THREE.LineSegments(wireframe, lineMaterial);
        boxOutline.position.set(
            this.container.width / 2,
            this.container.height / 2,
            this.container.depth / 2
        );
        this.scene.add(boxOutline);
    }

    handleResize() {
        this.camera.aspect = window.innerWidth / window.innerHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(window.innerWidth, window.innerHeight);
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        this.renderer.render(this.scene, this.camera);
    }
}

export default SceneManager;