import 'dart:developer';
import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:camera/camera.dart';
import 'package:image_picker/image_picker.dart';
import 'package:gal/gal.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'preferences.dart';

class MeasureItem extends StatefulWidget {
  const MeasureItem({super.key});

  @override
  MeasureItemState createState() => MeasureItemState();
}

class MeasureItemState extends State<MeasureItem> {
  CameraController? _controller;
  int _currentStep = 1; // 1 for first image, 2 for second image
  String? _firstImageB64;
  String? _secondImageB64;
  String? _firstPosition = 'top';
  String? _secondPosition = 'top';
  final TextEditingController _firstWidthController = TextEditingController();
  final TextEditingController _firstHeightController = TextEditingController();
  final TextEditingController _secondWidthController = TextEditingController();
  final TextEditingController _secondHeightController = TextEditingController();

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
    _firstWidthController.dispose();
    _firstHeightController.dispose();
    _secondWidthController.dispose();
    _secondHeightController.dispose();
    super.dispose();
  }

  void _showInstructionsDialog(BuildContext context) {
    showDialog(
      context: context,
      builder:
          (context) => AlertDialog(
            title: const Text('Instructions'),
            content: const Text(
              'Step 1: Capture the first image with a reference object.\n'
              'Step 2: Specify its position, height, and width, then click Confirm.\n'
              'Step 3: Capture the second image with the reference object.\n'
              'Step 4: Specify its position, height, and width, then click Confirm to get measurements.',
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
        await Gal.putImage(image.path); // Optional: save to gallery
      } else {
        final picker = ImagePicker();
        image = await picker.pickImage(source: ImageSource.gallery);
      }
      if (image != null) {
        final imageBytes = await image.readAsBytes();
        final imageB64 = base64Encode(imageBytes);
        setState(() {
          if (_currentStep == 1) {
            _firstImageB64 = imageB64;
          } else {
            _secondImageB64 = imageB64;
          }
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              '${_currentStep == 1 ? "First" : "Second"} image set.',
            ),
          ),
        );
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
    if (_currentStep == 1) {
      if (_firstImageB64 == null) {
        _showErrorDialog('Please set the first image.');
        return;
      }
      if (_firstWidthController.text.isEmpty ||
          _firstHeightController.text.isEmpty) {
        _showErrorDialog('Please enter width and height for the first image.');
        return;
      }
      setState(() {
        _currentStep = 2;
      });
    } else {
      if (_secondImageB64 == null) {
        _showErrorDialog('Please set the second image.');
        return;
      }
      if (_secondWidthController.text.isEmpty ||
          _secondHeightController.text.isEmpty) {
        _showErrorDialog('Please enter width and height for the second image.');
        return;
      }
      await _sendToApi();
    }
  }

  Future<void> _sendToApi() async {
    final firstWidth = double.tryParse(_firstWidthController.text);
    final firstHeight = double.tryParse(_firstHeightController.text);
    final secondWidth = double.tryParse(_secondWidthController.text);
    final secondHeight = double.tryParse(_secondHeightController.text);
    if (firstWidth == null ||
        firstHeight == null ||
        secondWidth == null ||
        secondHeight == null) {
      _showErrorDialog('Please enter valid width and height for both images.');
      return;
    }

    String frontImage;
    String sideImage;
    String refObjPos;

    if (_firstPosition == 'top' || _firstPosition == 'bottom') {
      frontImage = _firstImageB64!;
      sideImage = _secondImageB64!;
      refObjPos = _firstPosition!;
    } else if (_secondPosition == 'top' || _secondPosition == 'bottom') {
      frontImage = _secondImageB64!;
      sideImage = _firstImageB64!;
      refObjPos = _secondPosition!;
    } else {
      frontImage = _firstImageB64!;
      sideImage = _secondImageB64!;
      refObjPos = _firstPosition!;
    }

    final payload = {
      "front_image": frontImage,
      "side_image": sideImage,
      "ref_obj_pos": refObjPos,
      "ref_obj_width_real": 8.56,
      "ref_obj_width":
          (_firstPosition == 'top' || _firstPosition == 'bottom')
              ? firstWidth
              : secondWidth,
      "ref_obj_height":
          (_firstPosition == 'top' || _firstPosition == 'bottom')
              ? firstHeight
              : secondHeight,
    };

    try {
      final response = await http.post(
        Uri.parse('https://measurementsystem.up.railway.app/measure'),
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
                            'Height: ${result['height']} units\n'
                            'Depth: ${result['depth']} units',
                          ),
                          const SizedBox(height: 10),
                          if (result.containsKey('front_annotated_image') &&
                              result['front_annotated_image'] != null) ...[
                            const Text('Front Annotated Image:'),
                            const SizedBox(height: 5),
                            Image.memory(
                              base64Decode(result['front_annotated_image']),
                              width:
                                  double.infinity, // Take full available width
                              fit: BoxFit.contain, // Maintain aspect ratio
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
                              width:
                                  double.infinity, // Take full available width
                              fit: BoxFit.contain, // Maintain aspect ratio
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
                      onPressed: () {
                        Navigator.of(context).pop();
                        setState(() {
                          _currentStep = 1;
                          _firstImageB64 = null;
                          _secondImageB64 = null;
                        });
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
    // Get the selected unit from Preferences and map to abbreviation
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

    return Scaffold(
      resizeToAvoidBottomInset: true,
      appBar: _appBar(context),
      body: SingleChildScrollView(
        keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Text(
                _currentStep == 1
                    ? 'Step 1: Capture First Image'
                    : 'Step 2: Capture Second Image',
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
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text(
                    'Object Position:',
                    style: TextStyle(
                      fontSize: 18,
                      color: Colors.black87,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(width: 10),
                  SizedBox(
                    width: 120,
                    child: DropdownButtonFormField<String>(
                      value:
                          _currentStep == 1 ? _firstPosition : _secondPosition,
                      decoration: InputDecoration(
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                        contentPadding: const EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 8,
                        ),
                      ),
                      items: const [
                        DropdownMenuItem(value: 'top', child: Text('Top')),
                        DropdownMenuItem(value: 'right', child: Text('Right')),
                        DropdownMenuItem(
                          value: 'bottom',
                          child: Text('Bottom'),
                        ),
                        DropdownMenuItem(value: 'left', child: Text('Left')),
                      ],
                      onChanged: (value) {
                        setState(() {
                          if (_currentStep == 1) {
                            _firstPosition = value;
                          } else {
                            _secondPosition = value;
                          }
                        });
                      },
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),
              const Text(
                'Specify Reference Object Dimensions',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
              ),
              const SizedBox(height: 20),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _DimensionInputField(
                    label: 'Width ($unitLabel)',
                    controller:
                        _currentStep == 1
                            ? _firstWidthController
                            : _secondWidthController,
                  ),
                  _DimensionInputField(
                    label: 'Height ($unitLabel)',
                    controller:
                        _currentStep == 1
                            ? _firstHeightController
                            : _secondHeightController,
                  ),
                ],
              ),
              const SizedBox(height: 20),
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
                  _currentStep == 1
                      ? 'Confirm First Image'
                      : 'Confirm and Process',
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
    );
  }

  AppBar _appBar(BuildContext context) {
    return AppBar(
      title: const Text(
        'Setup Reference Object',
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

class _DimensionInputField extends StatelessWidget {
  final String label;
  final TextEditingController controller;

  const _DimensionInputField({required this.label, required this.controller});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(fontSize: 14, color: Colors.black87),
        ),
        const SizedBox(height: 8),
        SizedBox(
          width: 120,
          child: TextField(
            controller: controller,
            decoration: InputDecoration(
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8),
              ),
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 12,
                vertical: 8,
              ),
              hintText: 'Enter value',
              hintStyle: const TextStyle(color: Colors.black38),
            ),
            keyboardType: TextInputType.number,
          ),
        ),
      ],
    );
  }
}

void main() {
  runApp(MaterialApp(home: MeasureItem()));
}
