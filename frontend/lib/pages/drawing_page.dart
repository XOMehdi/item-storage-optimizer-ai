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
  final List<List<Offset>> polygons = [];
  final GlobalKey _imageKey = GlobalKey();
  ui.Image? _image;
  Size _actualImageSize = Size.zero;
  Size _displayedImageSize = Size.zero;
  Offset _imagePosition = Offset.zero;
  
  // This will store the actual display rect of the image accounting for BoxFit.contain
  Rect _imageDisplayRect = Rect.zero;

  @override
  void initState() {
    super.initState();
    _loadImage();
    // Add post-frame callback to calculate image dimensions after layout
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _updateImageDimensions();
    });
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
      // Get the container size
      final containerSize = box.size;
      
      // Calculate how the image fits within the container using BoxFit.contain
      if (_actualImageSize != Size.zero) {
        final imageAspectRatio = _actualImageSize.width / _actualImageSize.height;
        final containerAspectRatio = containerSize.width / containerSize.height;
        
        double imageWidth, imageHeight;
        double offsetX = 0, offsetY = 0;
        
        if (imageAspectRatio > containerAspectRatio) {
          // Image is wider than container (letterboxing - black bars on top and bottom)
          imageWidth = containerSize.width;
          imageHeight = containerSize.width / imageAspectRatio;
          offsetY = (containerSize.height - imageHeight) / 2;
        } else {
          // Image is taller than container (pillarboxing - black bars on sides)
          imageHeight = containerSize.height;
          imageWidth = containerSize.height * imageAspectRatio;
          offsetX = (containerSize.width - imageWidth) / 2;
        }
        
        setState(() {
          _displayedImageSize = Size(imageWidth, imageHeight);
          _imagePosition = box.localToGlobal(Offset.zero);
          _imageDisplayRect = Rect.fromLTWH(offsetX, offsetY, imageWidth, imageHeight);
        });
      }
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
    // If we don't have image dimensions yet, return a default
    if (_actualImageSize == Size.zero || _imageDisplayRect == Rect.zero) {
      return [0, 0];
    }

    // Calculate the point's position relative to the actual displayed image area
    // (accounting for letterboxing/pillarboxing)
    final relativeX = (localPoint.dx - _imageDisplayRect.left) / _imageDisplayRect.width;
    final relativeY = (localPoint.dy - _imageDisplayRect.top) / _imageDisplayRect.height;
    
    // Check if the point is within the image bounds
    if (relativeX < 0 || relativeX > 1 || relativeY < 0 || relativeY > 1) {
      return [0, 0]; // Point is outside the image area
    }
    
    // Convert to actual image coordinates
    final imageX = relativeX * _actualImageSize.width;
    final imageY = relativeY * _actualImageSize.height;
    
    return [imageX, imageY];
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

    // Convert polygons to the format expected by the API
    final formattedPolygons = polygons.map((polygon) {
      return polygon.map((point) => _normalizeCoordinate(point)).toList();
    }).toList();

    Navigator.pop(
      context,
      formattedPolygons,
    );
  }

  // Handle the tap gestures for drawing points
  void _onTapDown(TapDownDetails details) {
    // Make sure we have the latest image dimensions
    if (_imageDisplayRect == Rect.zero) {
      _updateImageDimensions();
      return; // Skip this tap if we're still calculating dimensions
    }

    final box = _imageKey.currentContext?.findRenderObject() as RenderBox?;
    if (box != null) {
      final localPos = box.globalToLocal(details.globalPosition);
      
      // Check if the tap is within the actual displayed image area
      if (localPos.dx >= _imageDisplayRect.left &&
          localPos.dx <= _imageDisplayRect.right &&
          localPos.dy >= _imageDisplayRect.top &&
          localPos.dy <= _imageDisplayRect.bottom) {
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
          // Recalculate image dimensions on layout changes
          WidgetsBinding.instance.addPostFrameCallback((_) {
            _updateImageDimensions();
          });
          
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
                // Add debug info to verify coordinates
                if (_imageDisplayRect != Rect.zero)
                  Positioned(
                    top: 16,
                    right: 16,
                    child: Container(
                      padding: const EdgeInsets.all(8),
                      color: Colors.black54,
                      child: Text(
                        'Image: ${_actualImageSize.width.toInt()}x${_actualImageSize.height.toInt()}\n'
                        'Display: ${_imageDisplayRect.width.toInt()}x${_imageDisplayRect.height.toInt()}',
                        style: const TextStyle(color: Colors.white, fontSize: 12),
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