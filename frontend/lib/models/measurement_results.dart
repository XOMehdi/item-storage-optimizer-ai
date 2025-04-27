class MeasurementResults {
  static final MeasurementResults _instance = MeasurementResults._internal();
  factory MeasurementResults() => _instance;
  MeasurementResults._internal();

  Map<String, dynamic>? data;
  List<List<num>>? placements;

  void initializeData() {
    data = {'container': {'width': 16, 'height': 8, 'depth': 4}, 'items': [], 'config': {}};
    // data = {'container': {}, 'items': [], 'config': {}};
    placements = [];
  }

  void setContainerData(double width, double height, double depth) {
    if (data == null) initializeData();
    data!['container'] = {'width': width, 'height': height, 'depth': depth};
  }

  void addItemData(int id, double width, double height, double depth) {
    if (data == null) initializeData();
    (data!['items'] as List).add({
      'id': id,
      'dimensions': {'width': width, 'height': height, 'depth': depth},
    });
  }

  void setConfigData({int populationSize = 30, int generations = 50}) {
    if (data == null) initializeData();
    data!['config'] = {
      'population_size': populationSize,
      'generations': generations,
    };
  }
}
