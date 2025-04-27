class Preferences {
  static final Preferences _instance = Preferences._internal();
  factory Preferences() => _instance;
  Preferences._internal();

  String measurementUnit = 'centimeter';
  bool drawSelection = false;
  bool showOutput = true;
}
