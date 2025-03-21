import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

class Preferences {
  static final Preferences _instance = Preferences._internal();
  factory Preferences() => _instance;
  Preferences._internal();

  String _measurementUnit = 'centimeter';
  bool _drawSelection = false;
  bool _showOutput = true;

  String get measurementUnit => _measurementUnit;
  set measurementUnit(String value) => _measurementUnit = value;

  bool get drawSelection => _drawSelection;
  set drawSelection(bool value) => _drawSelection = value;

  bool get showOutput => _showOutput;
  set showOutput(bool value) => _showOutput = value;
}

class PreferencesPage extends StatefulWidget {
  const PreferencesPage({super.key});

  @override
  _PreferencesPageState createState() => _PreferencesPageState();
}

class _PreferencesPageState extends State<PreferencesPage> {
  void _showInstructionsDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('Instructions'),
          content: const Text(
            'Adjust your preferences here to customize the app experience.',
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(context).pop();
              },
              child: const Text('Close'),
            ),
          ],
        );
      },
    );
  }

  AppBar _appBar(BuildContext context) {
    return AppBar(
      title: const Text(
        'Preferences',
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
        onTap: () {
          Navigator.pop(context);
        },
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
          onTap: () {
            _showInstructionsDialog(context);
          },
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

  final sectionDecoration = BoxDecoration(
    color: const Color(0xffF7F8F8),
    borderRadius: BorderRadius.circular(10),
    border: Border.all(color: const Color(0xffE0E0E0)),
    boxShadow: [
      BoxShadow(
        color: const Color(0xff1D1617).withOpacity(0.07),
        offset: const Offset(0, 10),
        blurRadius: 40,
        spreadRadius: 0,
      ),
    ],
  );

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: _appBar(context),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Measurement Unit
            Container(
              decoration: sectionDecoration,
              child: ListTile(
                contentPadding: const EdgeInsets.all(16),
                title: const Text(
                  'Measurement Unit',
                  style: TextStyle(fontSize: 16),
                ),
                trailing: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  decoration: BoxDecoration(
                    border: Border.all(color: const Color(0xffE0E0E0)),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: DropdownButton<String>(
                    value: Preferences().measurementUnit,
                    underline: const SizedBox(),
                    items:
                        ['centimeter', 'inches', 'meter'].map((String value) {
                          return DropdownMenuItem<String>(
                            value: value,
                            child: Text(value),
                          );
                        }).toList(),
                    onChanged: (String? newValue) {
                      if (newValue != null) {
                        setState(() {
                          Preferences().measurementUnit = newValue;
                        });
                      }
                    },
                  ),
                ),
              ),
            ),
            const SizedBox(height: 20),
            // Draw Selection section
            Container(
              decoration: sectionDecoration,
              child: SwitchListTile(
                title: const Text('Draw Selection'),
                value: Preferences().drawSelection,
                onChanged: (bool value) {
                  setState(() {
                    Preferences().drawSelection = value;
                  });
                },
                subtitle: Text(Preferences().drawSelection ? 'Yes' : 'No'),
              ),
            ),
            const SizedBox(height: 20),
            // Show Output section
            Container(
              decoration: sectionDecoration,
              child: SwitchListTile(
                title: const Text('Show Output'),
                value: Preferences().showOutput,
                onChanged: (bool value) {
                  setState(() {
                    Preferences().showOutput = value;
                  });
                },
                subtitle: Text(Preferences().showOutput ? 'Yes' : 'No'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
