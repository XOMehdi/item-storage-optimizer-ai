import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';

class DrawingPage extends StatefulWidget {
  final File imageFile;

  const DrawingPage({super.key, required this.imageFile});

  @override
  State<DrawingPage> createState() => _DrawingPageState();
}

class _DrawingPageState extends State<DrawingPage> {
  final List<Offset> _points = [];
  final List<List<Offset>> polygons = []; // Store polygons here
  final GlobalKey _imageKey = GlobalKey();
  ui.Image? _image;
  Size _actualImageSize = Size.zero;
  Size _displayedImageSize = Size.zero;
  Offset _imagePosition = Offset.zero;

  @override
  void initState() {
    super.initState();
    _loadImage();
  }

  // Load image and get its dimensions
  Future<void> _loadImage() async {
    final data = await widget.imageFile.readAsBytes();
    final decodedImage = await decodeImageFromList(data);
    setState(() {
      _image = decodedImage;
      _actualImageSize = Size(
        decodedImage.width.toDouble(),
        decodedImage.height.toDouble(),
      );
    });
  }

  // Store image layout information after it's laid out
  void _updateImageDimensions() {
    final box = _imageKey.currentContext?.findRenderObject() as RenderBox?;
    if (box != null) {
      setState(() {
        _displayedImageSize = box.size;
        _imagePosition = box.localToGlobal(Offset.zero);
      });
    }
  }

  // Undo the last point
  void _undoPoint() {
    setState(() {
      if (_points.isNotEmpty) {
        _points.removeLast();
      }
    });
  }

  // Complete the current polygon and start a new one
  void _completePolygon() {
    if (_points.length >= 3) {
      // Ensure we have at least 3 points for a valid polygon
      setState(() {
        polygons.add(
          List.from(_points),
        ); // Store the current set of points as a polygon
        _points.clear(); // Clear points for the next polygon
      });
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('A polygon needs at least 3 points'),
          duration: Duration(seconds: 2),
        ),
      );
    }
  }

  // Convert local coordinate to normalized coordinate based on actual image dimensions
  List<double> _normalizeCoordinate(Offset localPoint) {
    if (_displayedImageSize == Size.zero) return [0, 0];

    // Calculate scaling factors between the displayed image and actual image
    final scaleX = _actualImageSize.width / _displayedImageSize.width;
    final scaleY = _actualImageSize.height / _displayedImageSize.height;

    // Return pixel coordinates scaled to the actual image dimensions
    return [localPoint.dx * scaleX, localPoint.dy * scaleY];
  }

  // Finish drawing and return the polygons in the correct format
  void _finishDrawing() {
    // Complete current polygon if it has enough points
    if (_points.length >= 3) {
      _completePolygon();
    }

    if (polygons.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please draw at least one polygon'),
          duration: Duration(seconds: 2),
        ),
      );
      return;
    }

    // Convert polygons from List<Offset> to List<List<double>> with normalized coordinates
    final formattedPolygons =
        polygons.map((polygon) {
          return polygon.map((point) => _normalizeCoordinate(point)).toList();
        }).toList();

    Navigator.pop(
      context,
      formattedPolygons,
    ); // Pass the normalized polygons back
  }

  // Handle the tap gestures for drawing points
  void _onTapDown(TapDownDetails details) {
    if (_displayedImageSize == Size.zero) {
      _updateImageDimensions();
    }

    final box = _imageKey.currentContext?.findRenderObject() as RenderBox?;
    if (box != null) {
      final localPos = box.globalToLocal(details.globalPosition);

      // Check if the tap is within the image bounds
      if (localPos.dx >= 0 &&
          localPos.dx <= _displayedImageSize.width &&
          localPos.dy >= 0 &&
          localPos.dy <= _displayedImageSize.height) {
        setState(() {
          _points.add(localPos);
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const FittedBox(
          fit: BoxFit.scaleDown,
          child: Text(
            'Draw Polygons',
            style: TextStyle(
              color: Colors.black,
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.undo),
            onPressed: _undoPoint,
            tooltip: 'Undo',
          ),
          IconButton(
            icon: const Icon(Icons.check),
            onPressed: _completePolygon,
            tooltip: 'Complete Polygon',
          ),
          IconButton(
            icon: const Icon(Icons.done),
            onPressed: _finishDrawing,
            tooltip: 'Finish Drawing',
          ),
        ],
      ),
      body: LayoutBuilder(
        builder: (context, constraints) {
          return GestureDetector(
            onTapDown: _onTapDown,
            child: Stack(
              children: [
                Center(
                  child: Image.file(
                    widget.imageFile,
                    key: _imageKey,
                    fit: BoxFit.contain,
                    width: constraints.maxWidth,
                    height: constraints.maxHeight,
                  ),
                ),
                Positioned.fill(
                  child: CustomPaint(
                    painter: _PolygonPainter(
                      points: _points,
                      polygons: polygons,
                    ),
                  ),
                ),
                Positioned(
                  bottom: 16,
                  left: 16,
                  child: Container(
                    padding: const EdgeInsets.all(8),
                    color: Colors.black54,
                    child: Text(
                      'Points: ${_points.length} | Polygons: ${polygons.length}',
                      style: const TextStyle(color: Colors.white),
                    ),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _PolygonPainter extends CustomPainter {
  final List<Offset> points;
  final List<List<Offset>> polygons;

  _PolygonPainter({required this.points, required this.polygons});

  @override
  void paint(Canvas canvas, Size size) {
    final pointPaint =
        Paint()
          ..color = Colors.red
          ..strokeWidth = 2.0
          ..style = PaintingStyle.fill;

    final linePaint =
        Paint()
          ..color = Colors.blue
          ..strokeWidth = 2.0
          ..style = PaintingStyle.stroke;

    final polygonPaint =
        Paint()
          ..color = Colors.green.withAlpha((0.3 * 255).toInt())
          ..strokeWidth = 2.0
          ..style = PaintingStyle.fill;

    // Draw all polygons
    for (var polygon in polygons) {
      if (polygon.length >= 3) {
        final path = Path()..addPolygon(polygon, true);
        canvas.drawPath(path, polygonPaint);

        // Draw the outline of completed polygons
        canvas.drawPath(
          path,
          Paint()
            ..color = Colors.green
            ..strokeWidth = 2.0
            ..style = PaintingStyle.stroke,
        );

        // Draw the vertices of completed polygons
        for (final point in polygon) {
          canvas.drawCircle(point, 5, pointPaint..color = Colors.green);
        }
      }
    }

    // Draw the current points and lines
    if (points.isNotEmpty) {
      // Draw lines between points
      if (points.length > 1) {
        final path = Path()..moveTo(points.first.dx, points.first.dy);
        for (int i = 1; i < points.length; i++) {
          path.lineTo(points[i].dx, points[i].dy);
        }
        canvas.drawPath(path, linePaint);
      }

      // Draw the points
      for (final point in points) {
        canvas.drawCircle(point, 5, pointPaint..color = Colors.red);
      }
    }
  }

  @override
  bool shouldRepaint(covariant _PolygonPainter oldDelegate) => true;
}
