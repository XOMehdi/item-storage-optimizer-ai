class MeasurementResults {
  static final MeasurementResults _instance = MeasurementResults._internal();
  factory MeasurementResults() => _instance;
  MeasurementResults._internal();

  Map<String, dynamic>? data;

  void initializeData() {
    data = {'container': {}, 'items': [], 'config': {}};
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
