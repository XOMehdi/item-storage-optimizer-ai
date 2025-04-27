class ReferenceObject {
  static final ReferenceObject _instance = ReferenceObject._internal();
  factory ReferenceObject() => _instance;
  ReferenceObject._internal();

  String? referenceObjectPosition;
  double? referenceObjectWidth;
  double? referenceObjectHeight;
}
