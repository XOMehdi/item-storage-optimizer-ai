import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:item_storage_optimizer_ai/pages/home_page.dart';
import 'package:item_storage_optimizer_ai/models/preferences.dart';
import 'package:item_storage_optimizer_ai/models/reference_object.dart';

class SetupReferenceObject extends StatefulWidget {
  const SetupReferenceObject({super.key});

  @override
  SetupReferenceObjectState createState() => SetupReferenceObjectState();
}

class SetupReferenceObjectState extends State<SetupReferenceObject> {
  final TextEditingController _widthController = TextEditingController(
    text: ReferenceObject().referenceObjectWidth?.toString() ?? '',
  );
  final TextEditingController _heightController = TextEditingController(
    text: ReferenceObject().referenceObjectHeight?.toString() ?? '',
  );

  @override
  void initState() {
    super.initState();
  }

  @override
  void dispose() {
    _widthController.dispose();
    _heightController.dispose();
    super.dispose();
  }

  void _showInstructionsDialog(BuildContext context) {
    showDialog(
      context: context,
      builder:
          (context) => AlertDialog(
            title: const Text('Instructions'),
            content: const Text(
              'Step 1: Set the position of the reference object with respect to the item.\n'
              'Step 2: Set the real width for the reference object.\n'
              'Step 3: Set the real height for the reference object.\n',
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

  Future<void> _validateInputs() async {
    if (_widthController.text.isEmpty || _heightController.text.isEmpty) {
      _showErrorDialog(
        'Please enter the real width and height for the reference object.',
      );
      return;
    }

    setState(() {
      ReferenceObject().referenceObjectWidth = double.parse(
        _widthController.text,
      );
      ReferenceObject().referenceObjectHeight = double.parse(
        _heightController.text,
      );
    });

    Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => const HomePage()),
    );
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
      body: Center(
        child: SingleChildScrollView(
          keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
          child: Padding(
            padding: const EdgeInsets.all(20.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                const Text(
                  'Specify Reference Object Position & Dimensions:',
                  style: TextStyle(
                    fontSize: 18,
                    color: Colors.black87,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 60),
                const Text(
                  'Position',
                  style: TextStyle(fontSize: 14, color: Colors.black87),
                ),
                SizedBox(
                  width: 150,
                  child: DropdownButtonFormField<String>(
                    value: ReferenceObject().referenceObjectPosition,
                    decoration: InputDecoration(
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 8,
                      ),
                      hintText: 'Select value',
                      hintStyle: const TextStyle(color: Colors.black38),
                    ),
                    items: const [
                      DropdownMenuItem(value: 'left', child: Text('Left')),
                      DropdownMenuItem(value: 'right', child: Text('Right')),
                      DropdownMenuItem(value: 'top', child: Text('Top')),
                      DropdownMenuItem(value: 'bottom', child: Text('Bottom')),
                    ],
                    onChanged: (value) {
                      setState(() {
                        ReferenceObject().referenceObjectPosition = value;
                      });
                    },
                  ),
                ),
                const SizedBox(height: 20),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: [
                    _DimensionInputField(
                      label: 'Width ($unitLabel)',
                      controller: _widthController,
                    ),
                    _DimensionInputField(
                      label: 'Height ($unitLabel)',
                      controller: _heightController,
                    ),
                  ],
                ),
                const SizedBox(height: 40),
                ElevatedButton(
                  onPressed: _validateInputs,
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
                    'Confirm and Save',
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
      title: const FittedBox(
        fit: BoxFit.scaleDown,
        child: Text(
          'Setup Reference Object',
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
  runApp(MaterialApp(home: SetupReferenceObject()));
}
