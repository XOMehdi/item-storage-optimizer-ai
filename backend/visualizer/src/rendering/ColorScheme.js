import * as THREE from 'three';

class ColorScheme {
    static getColorFromIndex(index) {
        const hue = (index * 137.508) % 360; // Golden angle approximation
        return new THREE.Color(`hsl(${hue}, 70%, 60%)`);
    }

    static createItemTexture(id, color) {
        const canvas = document.createElement('canvas');
        canvas.width = 128;
        canvas.height = 128;
        const ctx = canvas.getContext('2d');

        // Draw label background
        ctx.fillStyle = color.getStyle();
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Draw ID text
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 48px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(`#${id}`, canvas.width / 2, canvas.height / 2);

        return new THREE.CanvasTexture(canvas);
    }
}
export default ColorScheme;
