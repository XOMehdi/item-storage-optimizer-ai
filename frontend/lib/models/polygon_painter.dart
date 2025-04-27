import 'package:flutter/material.dart';

class PolygonPainter extends CustomPainter {
  final List<List<Offset>> polygons;
  final List<Offset> currentPolygon;
  final bool drawSelection;

  PolygonPainter({
    required this.polygons,
    required this.currentPolygon,
    required this.drawSelection,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (!drawSelection) return;

    Paint completedPaint =
        Paint()
          ..color = Colors.green
          ..strokeWidth = 2.0
          ..style = PaintingStyle.stroke;

    for (var polygon in polygons) {
      if (polygon.length >= 2) {
        Path path = Path();
        path.moveTo(polygon[0].dx, polygon[0].dy);
        for (int i = 1; i < polygon.length; i++) {
          path.lineTo(polygon[i].dx, polygon[i].dy);
        }
        path.close();
        canvas.drawPath(path, completedPaint);
        for (var point in polygon) {
          canvas.drawCircle(point, 5, Paint()..color = Colors.green);
        }
      }
    }

    if (currentPolygon.isNotEmpty) {
      Paint currentPaint =
          Paint()
            ..color = Colors.yellow
            ..strokeWidth = 2.0
            ..style = PaintingStyle.stroke;
      Path path = Path();
      path.moveTo(currentPolygon[0].dx, currentPolygon[0].dy);
      for (int i = 1; i < currentPolygon.length; i++) {
        path.lineTo(currentPolygon[i].dx, currentPolygon[i].dy);
      }
      canvas.drawPath(path, currentPaint);
      for (var point in currentPolygon) {
        canvas.drawCircle(point, 5, Paint()..color = Colors.yellow);
      }
    }
  }

  @override
  bool shouldRepaint(covariant PolygonPainter oldDelegate) {
    return oldDelegate.polygons != polygons ||
        oldDelegate.currentPolygon != currentPolygon ||
        oldDelegate.drawSelection != drawSelection;
  }
}
