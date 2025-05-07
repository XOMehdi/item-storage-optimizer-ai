import 'dart:developer';
import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:image/image.dart' as img;
import 'package:item_storage_optimizer_ai/pages/home_page.dart';
import 'package:item_storage_optimizer_ai/models/preferences.dart';
import 'package:item_storage_optimizer_ai/models/reference_object.dart';
import 'package:item_storage_optimizer_ai/models/measurement_results.dart';
import 'package:item_storage_optimizer_ai/pages/camera_capture_page.dart';
import 'package:item_storage_optimizer_ai/pages/drawing_page.dart';

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
  final String? _refObjPos = ReferenceObject().referenceObjectPosition;
  final double? _refObjWidthReal = ReferenceObject().referenceObjectWidth;
  final double? _refObjHeightReal = ReferenceObject().referenceObjectHeight;

  int _itemCounter = 0;
  final bool _showOutput = Preferences().isShowOutput;
  bool _isDrawingMode = Preferences().isDrawingMode;

  List<Map<String, dynamic>> _scannedItems = [];

  @override
  void initState() {
    super.initState();
  }

  @override
  void dispose() {
    super.dispose();
  }

  Future<void> _captureImage(bool isSnapshot) async {
    try {
      File? imageFile;

      if (isSnapshot) {
        imageFile = await Navigator.push<File?>(
          context,
          MaterialPageRoute(builder: (_) => const CameraCapturePage()),
        );
      } else {
        final picker = ImagePicker();
        final pickedImage = await picker.pickImage(source: ImageSource.gallery);
        if (pickedImage != null) {
          imageFile = File(pickedImage.path);
        }
      }

      if (imageFile == null) return;

      // ⬇️ Decode to get image size
      final bytes = await imageFile.readAsBytes();
      final decoded = img.decodeImage(bytes);
      if (decoded == null) {
        log('Image decode failed', name: 'ImageDecoding');
        return;
      }
      final imageSize = Size(
        decoded.width.toDouble(),
        decoded.height.toDouble(),
      );

      if (_isDrawingMode) {
        final polygons = await Navigator.push<List<List<List<double>>>?>(
          context,
          MaterialPageRoute(builder: (_) => DrawingPage(imageFile: imageFile!)),
        );

        if (polygons != null) {
          _scannedItems.add({
            'image': imageFile,
            'polygons': polygons,
            'size': imageSize,
          });
          setState(() {}); // Refresh UI

          // Log polygon data for debugging
          log(
            'Image size: ${imageSize.width} x ${imageSize.height}',
            name: 'ImageCapture',
          );
          log('Polygon data: $polygons', name: 'PolygonData');
        }
      } else {
        _scannedItems.add({
          'image': imageFile,
          'polygons': null,
          'size': imageSize,
        });
        setState(() {});
      }
    } catch (e) {
      log('Error capturing image: $e', name: 'ImageCapture');

      if (!mounted) return;
      showDialog(
        context: context,
        builder:
            (_) => AlertDialog(
              title: const Text('Error'),
              content: Text('Failed to capture image: $e'),
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

  void _scanCompleted() {
    if (_itemCounter > 0) {
      showDialog(
        context: context,
        builder:
            (context) => AlertDialog(
              title: const Text('All Items Scanned'),
              content: const Text(
                'All items have been scanned successfully. Please proceed to the next step.',
              ),
              actions: [
                TextButton(
                  onPressed: () {
                    Navigator.pop(context);
                    Navigator.push(
                      context,
                      MaterialPageRoute(builder: (context) => HomePage()),
                    );
                  },
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
              title: const Text('No Items Scanned'),
              content: const Text(
                'Please scan at least one item before finishing.',
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
  }

  void _nextItem() {
    setState(() {
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
      final frontPolygons = frontItem['polygons'] as List<List<List<double>>>?;
      final sidePolygons = sideItem['polygons'] as List<List<List<double>>>?;

      log('Front polygon data: $frontPolygons', name: 'APIRequest');
      log('Side polygon data: $sidePolygons', name: 'APIRequest');

      final frontBytes = await frontImage.readAsBytes();
      final sideBytes = await sideImage.readAsBytes();
      final frontB64 = base64Encode(frontBytes);
      final sideB64 = base64Encode(sideBytes);

      final payload = {
        "front_image_b64": frontB64,
        "side_image_b64": sideB64,
        "ref_obj_pos": _refObjPos,
        "ref_obj_width_real": _refObjWidthReal,
        "ref_obj_height_real": _refObjHeightReal,
        "polygons_front_image": frontPolygons,
        "polygons_side_image": sidePolygons,
      };

      log(
        'Sending API request with payload: ${jsonEncode(payload)}',
        name: 'APIRequest',
      );

      final response = await http.post(
        Uri.parse('https://measurementsystem.up.railway.app/measure'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(payload),
      );

      log('API Response: ${response.statusCode}', name: 'APIResponse');
      log('API Response Body: ${response.body}', name: 'APIResponse');

      if (mounted) {
        Navigator.pop(context); // Close loading dialog
      }

      if (response.statusCode == 200) {
        final result = jsonDecode(response.body);
        if (result is Map<String, dynamic>) {
          _itemCounter++;
          MeasurementResults().addItemData(
            _itemCounter,
            result['width'],
            result['height'],
            result['depth'],
          );

          String unit = Preferences().measurementUnit;
          String unitLabel;
          switch (unit) {
            case 'centimeter':
              unitLabel = 'cm';
              break;
            case 'inches':
              unitLabel = 'in';
              break;
            case 'meter':
              unitLabel = 'm';
              break;
            default:
              unitLabel = 'cm'; // Fallback to 'cm' if unit is unrecognized
          }

          if (_showOutput) {
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
                              'Width: ${result['width'] ?? 'N/A'} $unitLabel\n'
                              'Height: ${result['height'] ?? 'N/A'} $unitLabel\n'
                              'Depth: ${result['depth'] ?? 'N/A'} $unitLabel',
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
                                    (context, error, stackTrace) => const Text(
                                      'Failed to load front image',
                                    ),
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
                    title: const Text('Measurement Successful'),
                    content: Text('Item Dimensions Stored.'),
                    actions: [
                      TextButton(
                        onPressed: () => Navigator.pop(context),
                        child: const Text('OK'),
                      ),
                    ],
                  ),
            );
          }
          // Clear the scanned items after successful processing
          setState(() {
            _scannedItems = [];
          });
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
                content: Text(
                  'Failed to scan item: ${response.statusCode}\n${response.body}',
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
    } catch (e) {
      log('Error in scan process: $e', name: 'ScanError');
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

  void _showInstructionsDialog(BuildContext context) {
    showDialog(
      context: context,
      builder:
          (context) => AlertDialog(
            title: const Text('Instructions'),
            content: SingleChildScrollView(
              child: Text(
                _isDrawingMode
                    ? '1. Click Capture to take the front image and draw polygons on it.\n'
                        '2. Click Complete Polygon when you finish drawing each shape, and then press Finish Drawing.\n'
                        '3. Click Capture again to take the side image and draw polygons.\n'
                        '4. Click Scan Item to send the data and see the results.\n'
                        '5. Click Next Item to reset and scan another item.'
                    : '1. Click Capture to take the front image (no polygons).\n'
                        '2. Click Capture again to take the side image (no polygons).\n'
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
        title: const FittedBox(
          fit: BoxFit.scaleDown,
          child: Text(
            'Scan Items',
            style: TextStyle(
              color: Colors.black,
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
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
              'assets/icons/arrow.svg',
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
                  value: _isDrawingMode,
                  onChanged: (value) {
                    setState(() {
                      _isDrawingMode = value;
                    });
                  },
                ),
              ],
            )
          else
            IconButton(
              icon: Icon(
                _isDrawingMode ? Icons.edit : Icons.edit_off,
                color: Colors.black,
              ),
              onPressed: () {
                setState(() {
                  _isDrawingMode = !_isDrawingMode;
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
                  'Capture from Camera',
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
                icon: const Icon(Icons.photo_library, color: Colors.white),
                label: const Text(
                  'Select from Gallery',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 8),
              child: Text(
                'Number of Items Scanned: $_itemCounter',
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 8),
              child: Text(
                'Number of Images Captured: ${_scannedItems.length}/2',
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
            if (_scannedItems.isNotEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 8),
                child: Text(
                  _scannedItems.length == 1
                      ? 'Front image captured'
                      : 'Front and side images captured',
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w500,
                    color: Colors.green,
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
                    icon: 'assets/icons/scan.svg',
                    label: 'Scan Item',
                    isSmallScreen: isSmallScreen,
                  ),
                  _buildActionButton(
                    onTap: _scanCompleted,
                    icon: 'assets/icons/correct.svg',
                    label: 'Finish Scan',
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
