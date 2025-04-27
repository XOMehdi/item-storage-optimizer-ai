import 'dart:developer';
import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:camera/camera.dart';
import 'package:frontend/pages/home_page.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:frontend/models/reference_object.dart';

class MeasureItemPage extends StatefulWidget {
  const MeasureItemPage({super.key});

  @override
  MeasureItemPageState createState() => MeasureItemPageState();
}

class MeasureItemPageState extends State<MeasureItemPage> {
  CameraController? _controller;
  String? _imageB64;
  final String? _refObjPos = ReferenceObject().referenceObjectPosition;
  final double? _refObjWidthReal = ReferenceObject().referenceObjectWidth;
  final double? _refObjHeightReal = ReferenceObject().referenceObjectHeight;

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
      );
      _controller = CameraController(backCamera, ResolutionPreset.high);
      await _controller!.initialize();
      if (mounted) setState(() {});
    } catch (e) {
      log('Error initializing camera: $e');
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  void _showInstructionsDialog(BuildContext context) {
    showDialog(
      context: context,
      builder:
          (context) => AlertDialog(
            title: const Text('Instructions'),
            content: const Text(
              'Step 1: Capture the image with a reference object.\n'
              'Step 2: click Confirm to get measurements.',
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('OK'),
              ),
            ],
          ),
    );
  }

  Future<void> _captureImage(bool isSnapshot) async {
    try {
      XFile? image;
      if (isSnapshot &&
          _controller != null &&
          _controller!.value.isInitialized) {
        image = await _controller!.takePicture();
      } else {
        final picker = ImagePicker();
        image = await picker.pickImage(source: ImageSource.gallery);
      }
      if (image != null) {
        final imageBytes = await image.readAsBytes();
        final imageB64 = base64Encode(imageBytes);
        setState(() {
          _imageB64 = imageB64;
        });
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Image is set.')));
      }
    } catch (e) {
      log('Error capturing image: $e');
      if (!mounted) return;
      showDialog(
        context: context,
        builder:
            (context) => AlertDialog(
              title: const Text('Error'),
              content: Text('Failed to capture image: $e'),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: const Text('OK'),
                ),
              ],
            ),
      );
    }
  }

  Future<void> _confirmAction() async {
    if (_imageB64 == null) {
      _showErrorDialog('Please set the image.');
      return;
    }
    await _sendToApi();
  }

  Future<void> _sendToApi() async {
    String image = _imageB64!;

    final payload = {
      "image_b64": image,
      "ref_obj_pos": _refObjPos,
      "ref_obj_width_real": _refObjWidthReal,
      "ref_obj_height_real": _refObjHeightReal,
      "polygons_image": null,
    };

    try {
      final response = await http.post(
        Uri.parse('https://measurementsystem.up.railway.app/measure2d'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(payload),
      );

      log('API Response: ${response.body}');

      if (response.statusCode == 200) {
        final result = jsonDecode(response.body);
        if (result.containsKey('error')) {
          _showErrorDialog('API Error: ${result['error']}');
        } else {
          showDialog(
            context: context,
            builder:
                (context) => AlertDialog(
                  title: const Text('Measurement Successful'),
                  content: SizedBox(
                    width:
                        MediaQuery.of(context).size.width *
                        0.9, // 90% of screen width
                    height:
                        MediaQuery.of(context).size.height *
                        0.8, // 80% of screen height
                    child: SingleChildScrollView(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Width: ${result['width']} units\n'
                            'Height: ${result['height']} units\n',
                          ),
                          const SizedBox(height: 10),
                          if (result.containsKey('annotated_image') &&
                              result['annotated_image'] != null) ...[
                            const Text('Annotated Image:'),
                            const SizedBox(height: 5),
                            Image.memory(
                              base64Decode(result['annotated_image']),
                              width:
                                  double.infinity, // Take full available width
                              fit: BoxFit.contain, // Maintain aspect ratio
                              errorBuilder:
                                  (context, error, stackTrace) =>
                                      const Text('Failed to load front image'),
                            ),
                          ],
                          const SizedBox(height: 10),
                        ],
                      ),
                    ),
                  ),
                  actions: [
                    TextButton(
                      onPressed: () {
                        Navigator.of(context).pop();
                        setState(() {
                          _imageB64 = null;
                        });
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const HomePage(),
                          ),
                        );
                      },
                      child: const Text('OK'),
                    ),
                  ],
                ),
          );
        }
      } else {
        _showErrorDialog('HTTP Error ${response.statusCode}: ${response.body}');
      }
    } catch (e) {
      _showErrorDialog('Request Failed: $e');
    }
  }

  void _showErrorDialog(String message) {
    showDialog(
      context: context,
      builder:
          (context) => AlertDialog(
            title: const Text('Error'),
            content: Text(message),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('OK'),
              ),
            ],
          ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      resizeToAvoidBottomInset: true,
      appBar: _appBar(context),
      body: SingleChildScrollView(
        keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: Center(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Text(
                  'Capture Image',
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 20),
                if (_controller != null && _controller!.value.isInitialized)
                  SizedBox(
                    height: MediaQuery.of(context).size.height * 0.44,
                    width: MediaQuery.of(context).size.width * 0.8,
                    child: CameraPreview(_controller!),
                  )
                else
                  Container(
                    height: MediaQuery.of(context).size.height * 0.44,
                    width: MediaQuery.of(context).size.width * 0.8,
                    color: Colors.grey,
                    child: const Center(child: CircularProgressIndicator()),
                  ),
                const SizedBox(height: 20),
                ElevatedButton.icon(
                  onPressed: () => _captureImage(true),
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
                  icon: SvgPicture.asset(
                    'assets/icons/camera1.svg',
                    height: 24,
                    width: 24,
                    color: Colors.black,
                  ),
                  label: const Text(
                    'Take Snapshot',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                  ),
                ),
                const SizedBox(height: 20),
                ElevatedButton.icon(
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
                const SizedBox(height: 40),
                ElevatedButton(
                  onPressed: _confirmAction,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xff2196F3),
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(
                      horizontal: 40,
                      vertical: 15,
                    ),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  child: Text(
                    'Confirm and Process',
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  AppBar _appBar(BuildContext context) {
    return AppBar(
      title: const Text(
        'Measure Item',
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
            'assets/icons/arrow.svg',
            height: 20,
            width: 20,
          ),
        ),
      ),
      actions: [
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
    );
  }
}

void main() {
  runApp(MaterialApp(home: MeasureItemPage()));
}
