class UIController {
    constructor(animationController) {
        this.animationController = animationController;
        this.elements = {
            itemCount: document.getElementById('itemCount'),
            currentItem: document.getElementById('currentItem'),
            playPauseButton: document.getElementById('play-pause-button'),
            stepBackButton: document.getElementById('stepback-button'),
            rewindButton: document.getElementById('rewind-button'),
            speedRange: document.getElementById('speed-range'),
            speedLabel: document.getElementById('speed-label'),
            helpButton: document.getElementById('help-button'),
            helpContent: document.getElementById('help-content'),
            loading: document.getElementById('loading')
        };

        this.initialize();
    }

    initialize() {
        // Set initial values
        this.elements.itemCount.textContent = this.animationController.itemRenderer.meshes.length;
        this.updateCounter(0, this.animationController.itemRenderer.meshes.length);

        // Set event handlers for animation controller
        this.animationController.onProgress = (current, total) => {
            this.updateCounter(current, total);
        };

        this.animationController.onPause = () => {
            this.elements.playPauseButton.textContent = '⏸️';
            this.elements.playPauseButton.style.backgroundColor = '';
        };

        this.animationController.onStepBack = () => {
            this.elements.stepBackButton.style.backgroundColor = '#f0d4f0';
            setTimeout(() => {
                this.elements.stepBackButton.style.backgroundColor = '';
            }, this.animationController.state.interval);
        };

        this.animationController.onRewind = () => {
            this.elements.rewindButton.style.backgroundColor = '#d4d4f7';
            setTimeout(() => {
                this.elements.rewindButton.style.backgroundColor = '';
            }, this.animationController.state.interval);
        };

        this.animationController.onSpeedChange = (speed) => {
            this.elements.speedLabel.textContent = `Speed: ${speed / 1000}x`;
        };

        // Set up UI event listeners
        this.elements.playPauseButton.addEventListener('click', () => {
            this.animationController.play();
            if (this.animationController.state.isPlaying) {
                this.elements.playPauseButton.textContent = '▶️';
                this.elements.playPauseButton.style.backgroundColor = '#d4f7d4';
            }
        });

        this.elements.stepBackButton.addEventListener('click', () => {
            this.animationController.stepBack();
        });

        this.elements.rewindButton.addEventListener('click', () => {
            this.animationController.rewind();
        });

        this.elements.speedRange.addEventListener('change', () => {
            const speed = parseInt(this.elements.speedRange.value);
            this.animationController.setSpeed(speed);
        });

        this.elements.helpButton.addEventListener('click', () => {
            this.toggleHelpContent();
        });

        // Hide loading indicator
        setTimeout(() => {
            this.elements.loading.style.display = 'none';
        }, 500);
    }

    updateCounter(current, total) {
        this.elements.currentItem.textContent = `${current} / ${total}`;
    }

    toggleHelpContent() {
        this.elements.helpContent.style.display =
            this.elements.helpContent.style.display === 'block' ? 'none' : 'block';
    }
}

export default UIController;