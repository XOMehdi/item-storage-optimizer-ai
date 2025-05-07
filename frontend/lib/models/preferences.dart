class Preferences {
  static final Preferences _instance = Preferences._internal();
  factory Preferences() => _instance;
  Preferences._internal();

  String measurementUnit = 'centimeter';
  bool isDrawingMode = false;
  bool isShowOutput = true;
}
