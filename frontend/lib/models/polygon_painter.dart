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

    const pointRadius = 8.0;

    // Paint for completed polygons
    final completedPaint =
        Paint()
          ..color = Colors.green.withOpacity(0.8)
          ..strokeWidth = 3.0
          ..style = PaintingStyle.stroke;

    final completedPointPaint =
        Paint()
          ..color = Colors.green
          ..style = PaintingStyle.fill;

    // Paint for in-progress polygon
    final currentPaint =
        Paint()
          ..color = Colors.yellow.withOpacity(0.8)
          ..strokeWidth = 3.0
          ..style = PaintingStyle.stroke;

    final currentPointPaint =
        Paint()
          ..color = Colors.yellow
          ..style = PaintingStyle.fill;

    // Draw completed polygons
    for (var polygon in polygons) {
      if (polygon.length >= 2) {
        // Draw lines
        final path = Path();
        path.moveTo(polygon[0].dx, polygon[0].dy);
        for (int i = 1; i < polygon.length; i++) {
          path.lineTo(polygon[i].dx, polygon[i].dy);
        }
        path.close();
        canvas.drawPath(path, completedPaint);

        // Draw points
        for (var point in polygon) {
          canvas.drawCircle(point, pointRadius, completedPointPaint);
        }
      }
    }

    // Draw current polygon being created
    if (currentPolygon.isNotEmpty) {
      // Draw lines between points
      if (currentPolygon.length >= 2) {
        final path = Path();
        path.moveTo(currentPolygon[0].dx, currentPolygon[0].dy);
        for (int i = 1; i < currentPolygon.length; i++) {
          path.lineTo(currentPolygon[i].dx, currentPolygon[i].dy);
        }
        canvas.drawPath(path, currentPaint);
      }

      // Draw points
      for (var point in currentPolygon) {
        canvas.drawCircle(point, pointRadius, currentPointPaint);
      }

      // Draw a dotted line from the last point to the first point if there are at least 3 points
      if (currentPolygon.length >= 3) {
        final dashPaint =
            Paint()
              ..color = Colors.yellow.withOpacity(0.5)
              ..strokeWidth = 2.0
              ..style = PaintingStyle.stroke;

        final dashPath = Path();
        dashPath.moveTo(currentPolygon.last.dx, currentPolygon.last.dy);
        dashPath.lineTo(currentPolygon.first.dx, currentPolygon.first.dy);

        canvas.drawPath(dashPath, dashPaint);
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
