import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:frontend/models/fuctionality_model.dart';
import 'package:tutorial_coach_mark/tutorial_coach_mark.dart';

class HomePage extends StatefulWidget {
  HomePage({super.key});

  @override
  _HomePageState createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final List<FunctionalityModel> functionalities =
      FunctionalityModel.getFunctionalities();

  final Map<String, String> routes = {
    'Setup Reference Object': '/setupReferenceObject',
    //  'Measure Item': '/measureItem',
    'Scan Item': '/scanItems',
    'Scan Storage Space': '/scanStorageSpace',
    'Preferences': '/Preferences',
  };

  late TutorialCoachMark tutorialCoachMark;
  List<TargetFocus> targets = [];
  final GlobalKey guideKey = GlobalKey();
  List<GlobalKey> functionalityKeys = [];

  @override
  void initState() {
    super.initState();
    functionalityKeys = List.generate(
      functionalities.length,
      (index) => GlobalKey(),
    );
    _initTutorial();

    WidgetsBinding.instance.addPostFrameCallback((_) => _showTutorial());
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
              return const Column(
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
                return Column(
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
      onFinish: () {
        print("Tutorial finished");
      },
      onSkip: () {
        print("Tutorial skipped");
        return true; // Explicitly return a bool value
      },
    );
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
      appBar: appBar(context),
      backgroundColor: Colors.white,
      body: ListView(
        children: [
          const SizedBox(height: 40),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Padding(
                padding: EdgeInsets.only(left: 20),
                child: Text(
                  'Item Storage Optimizer AI',
                  style: TextStyle(
                    color: Colors.black,
                    fontSize: 25,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              const SizedBox(height: 15),
              ListView.separated(
                itemCount: functionalities.length,
                shrinkWrap: true,
                separatorBuilder:
                    (context, index) => const SizedBox(height: 25),
                padding: const EdgeInsets.only(left: 20, right: 20),
                itemBuilder: (context, index) {
                  final functionality = functionalities[index];
                  return GestureDetector(
                    key: functionalityKeys[index],
                    onTap: () {
                      String? route = routes[functionality.name];
                      if (route != null) {
                        Navigator.pushNamed(context, route);
                      }
                    },
                    child: Container(
                      height: 100,
                      child: Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 16),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.center,
                          children: [
                            SvgPicture.asset(
                              functionality.iconPath,
                              width: 65,
                              height: 65,
                            ),
                            const SizedBox(width: 30),
                            Expanded(
                              child: Text(
                                functionality.name,
                                style: const TextStyle(
                                  fontWeight: FontWeight.w500,
                                  color: Colors.black,
                                  fontSize: 16,
                                ),
                                overflow: TextOverflow.ellipsis,
                                maxLines: 1,
                              ),
                            ),
                            SvgPicture.asset(
                              functionality.buttonPath,
                              width: 30,
                              height: 30,
                            ),
                          ],
                        ),
                      ),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(16),
                        boxShadow: [
                          BoxShadow(
                            color: const Color(0xff1D1617).withOpacity(0.07),
                            offset: const Offset(0, 10),
                            blurRadius: 40,
                            spreadRadius: 0,
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ],
          ),
          const SizedBox(height: 40),
        ],
      ),
    );
  }

  AppBar appBar(BuildContext context) {
    return AppBar(
      title: const Text(
        'Storage Optimizer',
        style: TextStyle(
          color: Colors.black,
          fontSize: 18,
          fontWeight: FontWeight.bold,
        ),
      ),
      backgroundColor: const Color.fromARGB(255, 255, 255, 255),
      elevation: 0.0,
      centerTitle: true,
      leading: GestureDetector(
        key: guideKey,
        onTap: () {
          _showTutorial();
        },
        child: Container(
          margin: const EdgeInsets.all(10),
          alignment: Alignment.center,
          child: SvgPicture.asset(
            'assets/icons/guide.svg',
            height: 20,
            width: 20,
          ),
          decoration: BoxDecoration(
            color: const Color(0xffF7F8F8),
            borderRadius: BorderRadius.circular(10),
          ),
        ),
      ),
      actions: [
        GestureDetector(
          onTap: () {},
          child: Container(
            margin: const EdgeInsets.all(10),
            alignment: Alignment.center,
            width: 37,
            child: SvgPicture.asset(
              'assets/icons/dots.svg',
              height: 5,
              width: 5,
            ),
            decoration: BoxDecoration(
              color: const Color(0xffF7F8F8),
              borderRadius: BorderRadius.circular(10),
            ),
          ),
        ),
      ],
    );
  }
}
