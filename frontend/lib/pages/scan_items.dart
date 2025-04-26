import 'dart:developer';

import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:camera/camera.dart';
import 'dart:io';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:image/image.dart' as img;

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const MaterialApp(home: ScanItemsPage()));
}

class ScanItemsPage extends StatefulWidget {
  const ScanItemsPage({super.key});

  @override
  ScanItemsPageState createState() => ScanItemsPageState();
}

class ScanItemsPageState extends State<ScanItemsPage> {
  CameraController? _controller;
  bool _isCameraInitialized = false;
  int dimensionCounter = 0;

  File? _currentImage;
  Size? _currentImageSize;
  List<List<Offset>> _currentPolygons = [];
  List<Offset> _currentPolygon = [];
  bool isDrawingMode = false;
  bool drawSelection = true;
  bool drawPolygonOrNot = false;

  List<Map<String, dynamic>> _scannedItems = [];

  @override
  void initState() {
    super.initState();
    _initializeCamera();
  }

  /// Initializes the camera
  Future<void> _initializeCamera() async {
    try {
      final cameras = await availableCameras();
      final backCamera = cameras.firstWhere(
        (camera) => camera.lensDirection == CameraLensDirection.back,
      );
      _controller = CameraController(backCamera, ResolutionPreset.high);
      await _controller!.initialize();
      if (mounted) {
        setState(() {
          _isCameraInitialized = true;
        });
      }
    } catch (e) {
      log('Error initializing camera: $e', name: 'CameraInitialization');
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  Future<void> _captureImage() async {
    if (!_controller!.value.isInitialized) return;
    try {
      final image = await _controller!.takePicture();
      final file = File(image.path);
      final bytes = await file.readAsBytes();
      final decodedImage = img.decodeImage(bytes);
      if (decodedImage == null) {
        log('Failed to decode image', name: 'ImageDecoding');
        return;
      }
      final originalSize = Size(
        decodedImage.width.toDouble(),
        decodedImage.height.toDouble(),
      );
      setState(() {
        _currentImage = file;
        _currentImageSize = originalSize;
        dimensionCounter++;
        if (drawPolygonOrNot) {
          isDrawingMode = true;
          _currentPolygons = [];
          _currentPolygon = [];
        } else {
          _scannedItems.add({
            'image': file,
            'polygons': null,
            'size': originalSize,
          });
          _currentImage = null;
          _currentImageSize = null;
        }
      });
    } catch (e) {
      log('Error capturing image: $e', name: 'ImageCapture');
    }
  }

  void _addPoint(Offset point) {
    setState(() {
      _currentPolygon.add(point);
    });
  }

  void _completePolygon() {
    if (_currentPolygon.length >= 3) {
      setState(() {
        _currentPolygons.add(List.from(_currentPolygon));
        _currentPolygon = [];
      });
    }
  }

  void _undoLastPoint() {
    setState(() {
      if (_currentPolygon.isNotEmpty) {
        _currentPolygon.removeLast();
      } else if (_currentPolygons.isNotEmpty) {
        _currentPolygon = _currentPolygons.removeLast();
      }
    });
  }

  void _finishDrawing() {
    if (_currentImage != null) {
      if (_currentPolygons.isNotEmpty || _currentPolygon.isNotEmpty) {
        setState(() {
          if (_currentPolygon.isNotEmpty) {
            _currentPolygons.add(List.from(_currentPolygon));
          }
          _scannedItems.add({
            'image': _currentImage!,
            'polygons': _currentPolygons,
            'size': _currentImageSize!,
          });
          isDrawingMode = false;
          _currentImage = null;
          _currentImageSize = null;
          _currentPolygons = [];
          _currentPolygon = [];
        });
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Please draw at least one polygon')),
        );
      }
    }
  }

  void _changeDimension() {
    if (_scannedItems.length >= 2) {
      showDialog(
        context: context,
        builder:
            (context) => AlertDialog(
              title: const Text('Images Complete'),
              content: const Text(
                'You have captured both images. Click Scan Item to proceed.',
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('OK'),
                ),
              ],
            ),
      );
    } else if (dimensionCounter < 1) {
      setState(() {
        dimensionCounter++;
      });
    }
  }

  void _nextItem() {
    setState(() {
      dimensionCounter = 0;
      _scannedItems = [];
    });
  }

  Future<void> _scanItem() async {
    if (_scannedItems.length != 2) {
      showDialog(
        context: context,
        builder:
            (context) => AlertDialog(
              title: const Text('Incomplete Scan'),
              content: const Text('Please capture both front and side images.'),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('OK'),
                ),
              ],
            ),
      );
      return;
    }

    // Show loading dialog
    showDialog(
      context: context,
      barrierDismissible: false,
      builder:
          (context) => const AlertDialog(
            content: Row(
              children: [
                CircularProgressIndicator(),
                SizedBox(width: 20),
                Text('Scanning...'),
              ],
            ),
          ),
    );

    try {
      final frontItem = _scannedItems[0];
      final sideItem = _scannedItems[1];
      final frontImage = frontItem['image'] as File;
      final sideImage = sideItem['image'] as File;
      final frontPolygons = frontItem['polygons'] as List<List<Offset>>?;
      final sidePolygons = sideItem['polygons'] as List<List<Offset>>?;
      final frontSize = frontItem['size'] as Size;
      final sideSize = sideItem['size'] as Size;

      final frontBytes = await frontImage.readAsBytes();
      final sideBytes = await sideImage.readAsBytes();
      final frontB64 = base64Encode(frontBytes);
      final sideB64 = base64Encode(sideBytes);

      const cw = 350.0;
      const ch = 540.0;
      final frontPolygonsTransformed = _transformPolygons(
        frontPolygons,
        cw,
        ch,
        frontSize,
      );
      final sidePolygonsTransformed = _transformPolygons(
        sidePolygons,
        cw,
        ch,
        sideSize,
      );

      final payload = {
        "front_image": frontB64,
        "side_image": sideB64,
        "ref_obj_pos": "left",
        "ref_obj_width_real": 8.56,
        "polygons_front_image": frontPolygonsTransformed,
        "polygons_side_image": sidePolygonsTransformed,
      };

      final response = await http.post(
        Uri.parse('https://measurementsystem.up.railway.app/measure'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(payload),
      );

      if (mounted) {
        Navigator.pop(context);
      }

      if (response.statusCode == 200) {
        final result = jsonDecode(response.body);
        if (result is Map<String, dynamic>) {
          showDialog(
            context: context,
            builder:
                (context) => AlertDialog(
                  title: const Text('Measurement Successful'),
                  content: SizedBox(
                    width: MediaQuery.of(context).size.width * 0.9,
                    height: MediaQuery.of(context).size.height * 0.8,
                    child: SingleChildScrollView(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Width: ${result['width'] ?? 'N/A'} units\n'
                            'Height: ${result['height'] ?? 'N/A'} units\n'
                            'Depth: ${result['depth'] ?? 'N/A'} units',
                          ),
                          const SizedBox(height: 10),
                          if (result.containsKey('front_annotated_image') &&
                              result['front_annotated_image'] != null) ...[
                            const Text('Front Annotated Image:'),
                            const SizedBox(height: 5),
                            Image.memory(
                              base64Decode(result['front_annotated_image']),
                              width: double.infinity,
                              fit: BoxFit.contain,
                              errorBuilder:
                                  (context, error, stackTrace) =>
                                      const Text('Failed to load front image'),
                            ),
                          ],
                          const SizedBox(height: 10),
                          if (result.containsKey('side_annotated_image') &&
                              result['side_annotated_image'] != null) ...[
                            const Text('Side Annotated Image:'),
                            const SizedBox(height: 5),
                            Image.memory(
                              base64Decode(result['side_annotated_image']),
                              width: double.infinity,
                              fit: BoxFit.contain,
                              errorBuilder:
                                  (context, error, stackTrace) =>
                                      const Text('Failed to load side image'),
                            ),
                          ],
                        ],
                      ),
                    ),
                  ),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.pop(context),
                      child: const Text('OK'),
                    ),
                  ],
                ),
          );
        } else {
          showDialog(
            context: context,
            builder:
                (context) => AlertDialog(
                  title: const Text('Error'),
                  content: const Text('Invalid response format'),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.pop(context),
                      child: const Text('OK'),
                    ),
                  ],
                ),
          );
        }
      } else {
        showDialog(
          context: context,
          builder:
              (context) => AlertDialog(
                title: const Text('Error'),
                content: Text('Failed to scan item: ${response.statusCode}'),
                actions: [
                  TextButton(
                    onPressed: () => Navigator.pop(context),
                    child: const Text('OK'),
                  ),
                ],
              ),
        );
      }
    } catch (e) {
      Navigator.pop(context);
      showDialog(
        context: context,
        builder:
            (context) => AlertDialog(
              title: const Text('Error'),
              content: Text('Error processing request: $e'),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('OK'),
                ),
              ],
            ),
      );
    }
  }

  /// Transforms polygon coordinates
  List<List<List<double>>>? _transformPolygons(
    List<List<Offset>>? polygons,
    double cw,
    double ch,
    Size imgSize,
  ) {
    if (polygons == null) return null;
    final iw = imgSize.width;
    final ih = imgSize.height;
    final s = (cw / iw < ch / ih) ? cw / iw : ch / ih;
    final offsetX = (cw - s * iw) / 2;
    final offsetY = (ch - s * ih) / 2;
    return polygons.map((polygon) {
      return polygon.map((point) {
        final x = (point.dx - offsetX) / s;
        final y = (point.dy - offsetY) / s;
        return [x, y];
      }).toList();
    }).toList();
  }

  void _showInstructionsDialog(BuildContext context) {
    showDialog(
      context: context,
      builder:
          (context) => AlertDialog(
            title: const Text('Instructions'),
            content: Text(
              drawPolygonOrNot
                  ? '1. Click Capture to take the front image and draw polygons on it.\n'
                      '2. Click Done to save it.\n'
                      '3. Click Change Dimension, then Capture to take the side image and draw polygons.\n'
                      '4. Click Done to save it.\n'
                      '5. Click Scan Item to send the data and see the results.\n'
                      '6. Click Next Item to reset and scan another item.'
                  : '1. Click Capture to take the front image (no polygons).\n'
                      '2. Click Change Dimension, then Capture to take the side image (no polygons).\n'
                      '3. Click Scan Item to send the data and see the results.\n'
                      '4. Click Next Item to reset and scan another item.',
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('OK'),
              ),
            ],
          ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Scan Items',
          style: TextStyle(
            color: Colors.black,
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        backgroundColor: Colors.white,
        elevation: 0.0,
        centerTitle: true,
        leading: GestureDetector(
          onTap: () => Navigator.pop(context),
          child: Container(
            margin: const EdgeInsets.all(10),
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: const Color(0xffF7F8F8),
              borderRadius: BorderRadius.circular(10),
            ),
            child: SvgPicture.asset(
              'assets/icons/Arrow.svg',
              height: 20,
              width: 20,
            ),
          ),
        ),
        actions: [
          Row(
            children: [
              const Text(
                'Draw Polygons',
                style: TextStyle(color: Colors.black),
              ),
              Switch(
                value: drawPolygonOrNot,
                onChanged: (value) {
                  setState(() {
                    drawPolygonOrNot = value;
                  });
                },
              ),
            ],
          ),
          GestureDetector(
            onTap: () => _showInstructionsDialog(context),
            child: Container(
              margin: const EdgeInsets.all(10),
              alignment: Alignment.center,
              width: 37,
              decoration: BoxDecoration(
                color: const Color(0xffF7F8F8),
                borderRadius: BorderRadius.circular(10),
              ),
              child: SvgPicture.asset(
                'assets/icons/dots.svg',
                height: 5,
                width: 5,
              ),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          if (!isDrawingMode)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 10),
              child: Text(
                _scannedItems.isEmpty
                    ? 'Please capture the front image'
                    : _scannedItems.length == 1
                    ? 'Please capture the side image'
                    : 'Ready to scan item',
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          Expanded(
            flex: 20,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(12),
                child: Container(
                  width: 350,
                  color: Colors.grey[300],
                  child:
                      isDrawingMode
                          ? _currentImage == null
                              ? const Center(child: Text('No image'))
                              : GestureDetector(
                                onTapDown: (details) {
                                  RenderBox renderBox =
                                      context.findRenderObject() as RenderBox;
                                  Offset localPosition = renderBox
                                      .globalToLocal(details.globalPosition);
                                  _addPoint(localPosition);
                                },
                                child: Stack(
                                  alignment: Alignment.center,
                                  children: [
                                    Image.file(
                                      _currentImage!,
                                      fit: BoxFit.contain,
                                    ),
                                    CustomPaint(
                                      size: Size.infinite,
                                      painter: PolygonPainter(
                                        polygons: _currentPolygons,
                                        currentPolygon: _currentPolygon,
                                        drawSelection: drawSelection,
                                      ),
                                    ),
                                  ],
                                ),
                              )
                          : _isCameraInitialized
                          ? CameraPreview(_controller!)
                          : const Center(child: CircularProgressIndicator()),
                ),
              ),
            ),
          ),
          if (isDrawingMode)
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                IconButton(
                  icon: const Icon(Icons.undo),
                  onPressed: _undoLastPoint,
                ),
                IconButton(
                  icon: const Icon(Icons.check),
                  onPressed: _completePolygon,
                ),
                ElevatedButton(
                  onPressed: _finishDrawing,
                  child: const Text('Done'),
                ),
                IconButton(
                  icon: Icon(
                    drawSelection ? Icons.visibility : Icons.visibility_off,
                  ),
                  onPressed: () {
                    setState(() {
                      drawSelection = !drawSelection;
                    });
                  },
                ),
              ],
            )
          else
            ElevatedButton.icon(
              onPressed: _captureImage,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xff4CAF50),
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(
                  horizontal: 30,
                  vertical: 12,
                ),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
              icon: const Icon(Icons.camera_alt, size: 20),
              label: const Text('Capture', style: TextStyle(fontSize: 18)),
            ),
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 10),
            child: Text(
              'Dimension Changes: $dimensionCounter',
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
            ),
          ),
          const Spacer(),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                GestureDetector(
                  onTap: _scanItem,
                  child: Column(
                    children: [
                      SvgPicture.asset(
                        'assets/icons/correct.svg',
                        width: 60,
                        height: 60,
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'Scan Item',
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                ),
                GestureDetector(
                  onTap: _changeDimension,
                  child: Column(
                    children: [
                      SvgPicture.asset(
                        'assets/icons/change.svg',
                        width: 60,
                        height: 60,
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'Change Dimension',
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                ),
                GestureDetector(
                  onTap: _nextItem,
                  child: Column(
                    children: [
                      SvgPicture.asset(
                        'assets/icons/next.svg',
                        width: 60,
                        height: 60,
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'Next Item',
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

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
