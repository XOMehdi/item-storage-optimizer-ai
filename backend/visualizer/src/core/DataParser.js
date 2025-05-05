import { Container, Item } from './Models.js'

class DataParser {
    static parseJSONWithFallback(jsonString) {
        try {
            return JSON.parse(jsonString);
        } catch (e) {
            try {
                return JSON.parse(decodeURIComponent(jsonString));
            } catch (e2) {
                console.error("Failed to parse JSON after decoding", e2);
                return null;
            }
        }
    }

    static parseUrlData() {
        const urlParams = new URLSearchParams(window.location.search);
        const containerParam = urlParams.get("container");
        const placementsParam = urlParams.get("placements");

        let containerData = [];
        let itemsData = [];

        if (containerParam) {
            containerData = this.parseJSONWithFallback(containerParam) || [];
        }

        if (placementsParam) {
            itemsData = this.parseJSONWithFallback(placementsParam) || [];
        }

        return {
            container: new Container(...containerData),
            items: itemsData.map(item => {
                if (!item || item.length < 7) return null;
                const [id, x, y, z, w, h, d] = item;
                return new Item(id, x, y, z, w, h, d);
            }).filter(item => item !== null)
        };
    }
}
export default DataParser;
