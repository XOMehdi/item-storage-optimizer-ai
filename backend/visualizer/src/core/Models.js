class Container {
    constructor(width, height, depth) {
        this.width = width;
        this.height = height;
        this.depth = depth;
    }
}

class Item {
    constructor(id, x, y, z, width, height, depth) {
        this.id = id;
        this.position = { x, y, z };
        this.dimensions = { width, height, depth };
    }

    get centerPosition() {
        return {
            x: this.position.x + this.dimensions.width / 2,
            y: this.position.y + this.dimensions.height / 2,
            z: this.position.z + this.dimensions.depth / 2
        };
    }
}


export { Container, Item };
