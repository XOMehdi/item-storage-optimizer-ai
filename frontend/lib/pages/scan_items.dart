import 'dart:developer';
import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:camera/camera.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:image/image.dart' as img;
import 'preferences.dart';
import 'setup_refrence_object.dart';

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
  final String? _refObjPos = ReferenceObject().referenceObjectPosition;
  final double? _refObjWidthReal = ReferenceObject().referenceObjectWidth;
  final double? _refObjHeightReal = ReferenceObject().referenceObjectHeight;

  File? _currentImage;
  Size? _currentImageSize;
  List<List<Offset>> _currentPolygons = [];
  List<Offset> _currentPolygon = [];
  bool isDrawingMode = false;
  bool drawSelection = Preferences().drawSelection;
  bool drawPolygonOrNot = false;

  List<Map<String, dynamic>> _scannedItems = [];

  @override
  void initState() {
    super.initState();
    _initializeCamera();
  }

  Future<void> _initializeCamera() async {
    try {
      final cameras = await availableCameras();
      final backCamera = cameras.firstWhere(
        (camera) => camera.lensDirection == CameraLensDirection.back,
        orElse: () => cameras.first,
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

  Future<void> _captureImage(bool isSnapshot) async {
    if (_controller == null || !_controller!.value.isInitialized) return;
    try {
      XFile? image;
      if (isSnapshot) {
        image = await _controller!.takePicture();
      } else {
        final picker = ImagePicker();
        image = await picker.pickImage(source: ImageSource.gallery);
      }

      if (image == null) return;

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

    await _sendToApi();
  }

  Future<void> _sendToApi() async {
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
                Expanded(child: Text('Scanning...')),
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

      // Calculate canvas dimensions based on screen size
      final mediaSize = MediaQuery.of(context).size;
      final cw = mediaSize.width * 0.8; // 80% of screen width
      final ch = mediaSize.height * 0.6; // 60% of screen height

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
        "front_image_b64": frontB64,
        "side_image_b64": sideB64,
        "ref_obj_pos": _refObjPos,
        "ref_obj_width_real": _refObjWidthReal,
        "ref_obj_height_real": _refObjHeightReal,
        "polygons_front_image": frontPolygonsTransformed,
        "polygons_side_image": sidePolygonsTransformed,
      };

      final response = await http.post(
        Uri.parse('https://measurementsystem.up.railway.app/measure'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(payload),
      );

      log('API Response: ${response.body}');

      if (mounted) {
        Navigator.pop(context); // Close loading dialog
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
                    height: MediaQuery.of(context).size.height * 0.7,
                    child: SingleChildScrollView(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Width: ${result['width'] ?? 'N/A'} units\n'
                            'Height: ${result['height'] ?? 'N/A'} units\n'
                            'Depth: ${result['depth'] ?? 'N/A'} units',
                            style: const TextStyle(fontSize: 16),
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
      if (mounted) {
        Navigator.pop(context); // Close loading dialog
      }
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
            content: SingleChildScrollView(
              child: Text(
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
    final Size screenSize = MediaQuery.of(context).size;
    final bool isSmallScreen = screenSize.width < 360;

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
            margin: const EdgeInsets.all(8),
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: const Color(0xffF7F8F8),
              borderRadius: BorderRadius.circular(10),
            ),
            child: SvgPicture.asset(
              'assets/icons/Arrow.svg',
              height: 18,
              width: 18,
              fit: BoxFit.contain,
            ),
          ),
        ),
        actions: [
          if (!isSmallScreen)
            Row(
              children: [
                const Text(
                  'Draw Polygons',
                  style: TextStyle(color: Colors.black, fontSize: 14),
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
            )
          else
            IconButton(
              icon: Icon(
                drawPolygonOrNot ? Icons.edit : Icons.edit_off,
                color: Colors.black,
              ),
              onPressed: () {
                setState(() {
                  drawPolygonOrNot = !drawPolygonOrNot;
                });
              },
              tooltip: 'Toggle Draw Polygons',
            ),
          IconButton(
            icon: const Icon(Icons.help_outline, color: Colors.black),
            onPressed: () => _showInstructionsDialog(context),
            tooltip: 'Instructions',
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            if (!isDrawingMode)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 8),
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
              flex: 3,
              child: Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 8,
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(12),
                  child: Container(
                    width: double.infinity,
                    color: Colors.grey[300],
                    child:
                        isDrawingMode
                            ? _currentImage == null
                                ? const Center(child: Text('No image'))
                                : GestureDetector(
                                  onTapDown: (details) {
                                    final RenderBox renderBox =
                                        context.findRenderObject() as RenderBox;
                                    final Offset localPosition = renderBox
                                        .globalToLocal(details.globalPosition);
                                    _addPoint(localPosition);
                                  },
                                  child: Stack(
                                    alignment: Alignment.center,
                                    children: [
                                      Image.file(
                                        _currentImage!,
                                        fit: BoxFit.contain,
                                        width: double.infinity,
                                        height: double.infinity,
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
                            ? ClipRRect(
                              borderRadius: BorderRadius.circular(12),
                              child: AspectRatio(
                                aspectRatio: _controller!.value.aspectRatio,
                                child: CameraPreview(_controller!),
                              ),
                            )
                            : const Center(child: CircularProgressIndicator()),
                  ),
                ),
              ),
            ),
            if (isDrawingMode)
              Container(
                padding: const EdgeInsets.symmetric(vertical: 8),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    IconButton(
                      icon: const Icon(Icons.undo),
                      onPressed: _undoLastPoint,
                      tooltip: 'Undo Last Point',
                    ),
                    IconButton(
                      icon: const Icon(Icons.check),
                      onPressed: _completePolygon,
                      tooltip: 'Complete Polygon',
                    ),
                    ElevatedButton(
                      onPressed: _finishDrawing,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xff4CAF50),
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                      ),
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
                      tooltip: 'Toggle Visibility',
                    ),
                  ],
                ),
              )
            else
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 8),
                child: ElevatedButton.icon(
                  onPressed: () => _captureImage(true),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xff4CAF50),
                    foregroundColor: Colors.white,
                    padding: EdgeInsets.symmetric(
                      horizontal: isSmallScreen ? 20 : 30,
                      vertical: 12,
                    ),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  icon: const Icon(Icons.camera_alt, size: 20),
                  label: Text(
                    'Capture',
                    style: TextStyle(fontSize: isSmallScreen ? 16 : 18),
                  ),
                ),
              ),
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 8),
              child: ElevatedButton.icon(
                onPressed: () => _captureImage(false),
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
                icon: const Icon(Icons.photo_library, color: Colors.black),
                label: const Text(
                  'Select from Gallery',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 8),
              child: Text(
                'Dimension Changes: $dimensionCounter',
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
            const Spacer(),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  _buildActionButton(
                    onTap: _scanItem,
                    icon: 'assets/icons/correct.svg',
                    label: 'Scan Item',
                    isSmallScreen: isSmallScreen,
                  ),
                  _buildActionButton(
                    onTap: _changeDimension,
                    icon: 'assets/icons/change.svg',
                    label: 'Change Dimension',
                    isSmallScreen: isSmallScreen,
                  ),
                  _buildActionButton(
                    onTap: _nextItem,
                    icon: 'assets/icons/next.svg',
                    label: 'Next Item',
                    isSmallScreen: isSmallScreen,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildActionButton({
    required VoidCallback onTap,
    required String icon,
    required String label,
    required bool isSmallScreen,
  }) {
    return Expanded(
      child: GestureDetector(
        onTap: onTap,
        child: Column(
          children: [
            SvgPicture.asset(
              icon,
              width: isSmallScreen ? 40 : 50,
              height: isSmallScreen ? 40 : 50,
              fit: BoxFit.contain,
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(
                fontSize: isSmallScreen ? 12 : 14,
                fontWeight: FontWeight.w500,
              ),
              textAlign: TextAlign.center,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
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
