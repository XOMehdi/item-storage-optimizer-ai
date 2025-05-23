class FunctionalityModel {
  final String name;
  final String iconPath;
  final String buttonPath;
  final bool boxIsSelected;

  FunctionalityModel({
    required this.name,
    required this.iconPath,
    required this.buttonPath,
    required this.boxIsSelected,
  });

  static List<FunctionalityModel> getFunctionalities() {
    return [
      FunctionalityModel(
        name: 'Setup Reference Object',
        iconPath: 'assets/icons/id-card.svg',
        buttonPath: 'assets/icons/button.svg',
        boxIsSelected: false,
      ),
      FunctionalityModel(
        name: 'Measure Item',
        iconPath: 'assets/icons/measure.svg',
        buttonPath: 'assets/icons/button.svg',
        boxIsSelected: false,
      ),
      FunctionalityModel(
        name: 'Scan Items',
        iconPath: 'assets/icons/scanner.svg',
        buttonPath: 'assets/icons/button.svg',
        boxIsSelected: false,
      ),
      FunctionalityModel(
        name: 'Scan Storage Space',
        iconPath: 'assets/icons/suitcase.svg',
        buttonPath: 'assets/icons/button.svg',
        boxIsSelected: false,
      ),
      FunctionalityModel(
        name: 'Start Optimization',
        iconPath: 'assets/icons/optimize.svg',
        buttonPath: 'assets/icons/button.svg',
        boxIsSelected: false,
      ),
      FunctionalityModel(
        name: 'Visualize Packing',
        iconPath: 'assets/icons/visualize.svg',
        buttonPath: 'assets/icons/button.svg',
        boxIsSelected: false,
      ),
      FunctionalityModel(
        name: 'Preferences',
        iconPath: 'assets/icons/settings.svg',
        buttonPath: 'assets/icons/button.svg',
        boxIsSelected: false,
      ),
    ];
  }
}
