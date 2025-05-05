import Config from '../core/Config.js';

class AnimationController {
    constructor(itemRenderer) {
        this.itemRenderer = itemRenderer;
        this.state = {
            currentIndex: 0,
            isPlaying: false,
            interval: Config.ANIMATION.DEFAULT_INTERVAL,
            timer: null
        };
    }

    play() {
        if (this.state.currentIndex >= this.itemRenderer.meshes.length) return;

        if (this.state.isPlaying) {
            this.pause();
            return;
        }

        this.state.isPlaying = true;
        this.state.timer = setInterval(() => {
            if (this.state.currentIndex < this.itemRenderer.meshes.length) {
                this.itemRenderer.showItem(this.state.currentIndex);
                this.state.currentIndex++;
                this.onProgress(this.state.currentIndex, this.itemRenderer.meshes.length);
            } else {
                this.pause();
            }
        }, this.state.interval);
    }

    pause() {
        this.state.isPlaying = false;
        clearInterval(this.state.timer);
        this.onPause();
    }

    stepBack() {
        if (this.state.currentIndex <= 0) return;

        this.state.currentIndex--;
        this.itemRenderer.hideItem(this.state.currentIndex);
        this.onProgress(this.state.currentIndex, this.itemRenderer.meshes.length);
        this.onStepBack();
    }

    rewind() {
        this.pause();
        this.itemRenderer.hideAllItems();
        this.state.currentIndex = 0;
        this.onProgress(this.state.currentIndex, this.itemRenderer.meshes.length);
        this.onRewind();
    }

    setSpeed(speed) {
        speed = Math.max(Config.ANIMATION.MIN_SPEED, Math.min(Config.ANIMATION.MAX_SPEED, speed));

        // Calculate interval using linear interpolation
        const range = Config.ANIMATION.MAX_SPEED - Config.ANIMATION.MIN_SPEED;
        this.state.interval = Config.ANIMATION.MAX_SPEED -
            ((speed - Config.ANIMATION.MIN_SPEED) *
                (Config.ANIMATION.MAX_SPEED - Config.ANIMATION.MIN_SPEED) / range);

        this.state.interval = Math.round(this.state.interval);

        // Restart timer if playing
        if (this.state.isPlaying) {
            clearInterval(this.state.timer);
            this.state.timer = setInterval(() => {
                if (this.state.currentIndex < this.itemRenderer.meshes.length) {
                    this.itemRenderer.showItem(this.state.currentIndex);
                    this.state.currentIndex++;
                    this.onProgress(this.state.currentIndex, this.itemRenderer.meshes.length);
                } else {
                    this.pause();
                }
            }, this.state.interval);
        }

        this.onSpeedChange(speed);
    }

    // Event handlers (to be set by UI controller)
    onProgress = (current, total) => { };
    onPause = () => { };
    onStepBack = () => { };
    onRewind = () => { };
    onSpeedChange = (speed) => { };
}

export default AnimationController;