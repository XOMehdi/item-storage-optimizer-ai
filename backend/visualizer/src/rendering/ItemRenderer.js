import ColorScheme from './ColorScheme.js';

class ItemRenderer {
    constructor(scene, items) {
        this.scene = scene;
        this.items = items;
        this.meshes = [];

        this.createMeshes();
    }

    createMeshes() {
        this.meshes = this.items.map((item, index) => {
            const baseColor = ColorScheme.getColorFromIndex(index);
            const texture = ColorScheme.createItemTexture(item.id, baseColor);

            // Create materials
            const materials = [
                new THREE.MeshStandardMaterial({ map: texture }), // right
                new THREE.MeshStandardMaterial({ map: texture }), // left
                new THREE.MeshStandardMaterial({ map: texture }), // top
                new THREE.MeshStandardMaterial({ map: texture }), // bottom
                new THREE.MeshStandardMaterial({ map: texture }), // front
                new THREE.MeshStandardMaterial({ map: texture })  // back
            ];

            // Create geometry
            const geometry = new THREE.BoxGeometry(
                item.dimensions.width,
                item.dimensions.height,
                item.dimensions.depth
            );

            // Create mesh
            const mesh = new THREE.Mesh(geometry, materials);
            mesh.position.set(
                item.centerPosition.x,
                item.centerPosition.y,
                item.centerPosition.z
            );
            mesh.visible = false;

            this.scene.add(mesh);
            return mesh;
        });

        return this.meshes;
    }

    showItem(index) {
        if (index >= 0 && index < this.meshes.length) {
            this.meshes[index].visible = true;
        }
    }

    hideItem(index) {
        if (index >= 0 && index < this.meshes.length) {
            this.meshes[index].visible = false;
        }
    }

    hideAllItems() {
        this.meshes.forEach(mesh => {
            mesh.visible = false;
        });
    }
}
export default ItemRenderer;
