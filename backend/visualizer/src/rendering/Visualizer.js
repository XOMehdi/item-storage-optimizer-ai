import DataParser from '../core/DataParser.js';
import SceneManager from './SceneManager.js';
import ItemRenderer from './ItemRenderer.js';
import AnimationController from '../controls/AnimationController.js';
import UIController from '../controls/UIController.js';

class Visualizer {
    visualize() {
        // Parse URL data
        const { container, items } = DataParser.parseUrlData();

        // Initialize scene
        this.sceneManager = new SceneManager(container);

        // Initialize item renderer
        this.itemRenderer = new ItemRenderer(this.sceneManager.scene, items);

        // Initialize animation controller
        this.animationController = new AnimationController(this.itemRenderer);

        // Initialize UI controller
        this.uiController = new UIController(this.animationController);

        // Start animation loop
        this.sceneManager.animate();
    }
}

export default Visualizer;
