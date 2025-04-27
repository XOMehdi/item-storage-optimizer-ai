import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:frontend/models/fuctionality_model.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tutorial_coach_mark/tutorial_coach_mark.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  HomePageState createState() => HomePageState();
}

class HomePageState extends State<HomePage> {
  final List<FunctionalityModel> functionalities =
      FunctionalityModel.getFunctionalities();

  final Map<String, String> routes = {
    'Setup Reference Object': '/setupReferenceObject',
    'Measure Item': '/measureItem',
    'Scan Item': '/scanItems',
    'Scan Storage Space': '/scanStorageSpace',
    'Preferences': '/preferences',
  };

  late TutorialCoachMark tutorialCoachMark;
  List<TargetFocus> targets = [];
  final GlobalKey guideKey = GlobalKey();
  List<GlobalKey> functionalityKeys = [];
  bool _isFirstLaunch = true;

  @override
  void initState() {
    super.initState();
    functionalityKeys = List.generate(
      functionalities.length,
      (index) => GlobalKey(),
    );
    _initTutorial();
    _checkFirstLaunch();
  }

  void _initTutorial() {
    targets.add(
      TargetFocus(
        identify: "Guide Button",
        keyTarget: guideKey,
        contents: [
          TargetContent(
            align: ContentAlign.bottom,
            builder: (context, controller) {
              return Container(
                constraints: const BoxConstraints(maxWidth: 300),
                child: const Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      "Guide Button",
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                        fontSize: 20,
                      ),
                    ),
                    Padding(
                      padding: EdgeInsets.only(top: 10.0),
                      child: Text(
                        "Tap here to start the tutorial and learn about the app's features.",
                        style: TextStyle(color: Colors.white),
                      ),
                    ),
                  ],
                ),
              );
            },
          ),
        ],
      ),
    );

    for (int i = 0; i < functionalities.length; i++) {
      targets.add(
        TargetFocus(
          identify: functionalities[i].name,
          keyTarget: functionalityKeys[i],
          shape: ShapeLightFocus.RRect,
          radius: 16,
          contents: [
            TargetContent(
              align: ContentAlign.top,
              builder: (context, controller) {
                return Container(
                  constraints: const BoxConstraints(maxWidth: 300),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        functionalities[i].name,
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                          fontSize: 20,
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.only(top: 10.0),
                        child: Text(
                          _getFunctionalityDescription(functionalities[i].name),
                          style: const TextStyle(color: Colors.white),
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),
          ],
        ),
      );
    }

    tutorialCoachMark = TutorialCoachMark(
      targets: targets,
      colorShadow: Colors.grey,
      textSkip: "SKIP",
      paddingFocus: 5,
      opacityShadow: 0.8,
      onFinish: () {},
      onSkip: () {
        return true;
      },
    );
  }

  Future<void> _checkFirstLaunch() async {
    final prefs = await SharedPreferences.getInstance();
    _isFirstLaunch = prefs.getBool('first_launch') ?? true;

    if (_isFirstLaunch) {
      // Show a small welcome message with "Start Tour" button
      WidgetsBinding.instance.addPostFrameCallback((_) {
        showDialog(
          context: context,
          builder:
              (context) => AlertDialog(
                title: const Text('Welcome to Storage Optimizer'),
                content: const Text(
                  'Would you like to take a quick tour of the app?',
                ),
                actions: [
                  TextButton(
                    onPressed: () {
                      Navigator.pop(context);
                      _showTutorial();
                      prefs.setBool('first_launch', false);
                    },
                    child: const Text('Yes, show me around'),
                  ),
                  TextButton(
                    onPressed: () {
                      Navigator.pop(context);
                      prefs.setBool('first_launch', false);
                    },
                    child: const Text('Skip'),
                  ),
                ],
              ),
        );
      });
    }
  }

  void _showTutorial() {
    tutorialCoachMark.show(context: context);
  }

  String _getFunctionalityDescription(String name) {
    switch (name) {
      case 'Setup Reference Object':
        return "Set up a reference object to calibrate the scanning system.";
      case 'Scan Item':
        return "Scan items to analyze their dimensions and properties.";
      case 'Scan Storage Space':
        return "Scan your storage area to optimize space usage.";
      case 'Preferences':
        return "Adjust app preferences and configurations.";
      default:
        return "This feature helps you with storage optimization.";
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: _buildAppBar(context),
      backgroundColor: Colors.white,
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            return SingleChildScrollView(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const SizedBox(height: 24),
                    const Padding(
                      padding: EdgeInsets.only(left: 4),
                      child: Text(
                        'Item Storage Optimizer AI',
                        style: TextStyle(
                          color: Colors.black,
                          fontSize: 22,
                          fontWeight: FontWeight.w600,
                        ),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    const SizedBox(height: 15),
                    ListView.separated(
                      physics: const NeverScrollableScrollPhysics(),
                      itemCount: functionalities.length,
                      shrinkWrap: true,
                      separatorBuilder:
                          (context, index) => const SizedBox(height: 16),
                      itemBuilder: (context, index) {
                        final functionality = functionalities[index];
                        return _buildFunctionalityCard(functionality, index);
                      },
                    ),
                    const SizedBox(height: 24),
                  ],
                ),
              ),
            );
          },
        ),
      ),
    );
  }

  Widget _buildFunctionalityCard(FunctionalityModel functionality, int index) {
    return GestureDetector(
      key: functionalityKeys[index],
      onTap: () {
        String? route = routes[functionality.name];
        if (route != null) {
          Navigator.pushNamed(context, route);
        }
      },
      child: Container(
        height: 90,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
              color: const Color(0xff1D1617).withAlpha((0.07 * 255).toInt()),
              offset: const Offset(0, 10),
              blurRadius: 40,
              spreadRadius: 0,
            ),
          ],
        ),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              SvgPicture.asset(
                functionality.iconPath,
                width: 50,
                height: 50,
                fit: BoxFit.contain,
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Text(
                  functionality.name,
                  style: const TextStyle(
                    fontWeight: FontWeight.w500,
                    color: Colors.black,
                    fontSize: 15,
                  ),
                  overflow: TextOverflow.ellipsis,
                  maxLines: 2,
                ),
              ),
              const SizedBox(width: 8),
              SvgPicture.asset(
                functionality.buttonPath,
                width: 24,
                height: 24,
                fit: BoxFit.contain,
              ),
            ],
          ),
        ),
      ),
    );
  }

  AppBar _buildAppBar(BuildContext context) {
    return AppBar(
      title: const FittedBox(
        fit: BoxFit.scaleDown,
        child: Text(
          'Storage Optimizer',
          style: TextStyle(
            color: Colors.black,
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
      backgroundColor: Colors.white,
      elevation: 0.5,
      centerTitle: true,
      leading: GestureDetector(
        key: guideKey,
        onTap: _showTutorial,
        child: Container(
          margin: const EdgeInsets.all(8),
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: const Color(0xffF7F8F8),
            borderRadius: BorderRadius.circular(10),
          ),
          child: SvgPicture.asset(
            'assets/icons/guide.svg',
            height: 20,
            width: 20,
            fit: BoxFit.contain,
          ),
        ),
      ),
      actions: [
        GestureDetector(
          onTap: () {},
          child: Container(
            margin: const EdgeInsets.all(8),
            alignment: Alignment.center,
            width: 36,
            decoration: BoxDecoration(
              color: const Color(0xffF7F8F8),
              borderRadius: BorderRadius.circular(10),
            ),
            child: SvgPicture.asset(
              'assets/icons/dots.svg',
              height: 5,
              width: 5,
              fit: BoxFit.contain,
            ),
          ),
        ),
      ],
    );
  }
}
